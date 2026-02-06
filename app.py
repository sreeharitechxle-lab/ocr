import os
import re
import time
import requests
import logging
from flask import Flask, render_template, request, flash, send_file, redirect, url_for
import pandas as pd
from io import BytesIO
from pymongo import MongoClient
from bson.objectid import ObjectId
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.secret_key = "supersecretkey" # Needed for flashing messages

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from extraction import extract_business_card_details

UPLOAD_FOLDER = "uploads"

# ---------------- MONGODB CONFIGURATION ----------------
# Use environment variable for MongoDB URI (for Render deployment)
# Falls back to localhost for local development
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")

try:
    client = MongoClient(MONGO_URI)
    db = client["business_card_db"]
    collection = db["cards"]
    logger.info(f"Connected to MongoDB successfully at {MONGO_URI[:20]}...")
except Exception as e:
    logger.error(f"Failed to connect to MongoDB: {e}")

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ---------------- COMPRESTO IMAGE COMPRESSION API ----------------
def compress_image(image_path):
    """
    Compresses image using the Compresto API (compresto.app).
    Returns the path to the compressed image (overwrites original).
    """
    api_key = os.getenv("COMPRESTO_API_KEY")
    if not api_key:
        logger.error("COMPRESTO_API_KEY not found in environment")
        return image_path

    url = "https://api.compresto.app/v1/compress"
    headers = {"X-API-Key": api_key}
    
    try:
        logger.info(f"Sending {image_path} to Compresto API for compression...")
        
        # Prepare parameters: quality=80 (default API behavior usually optimized)
        # The API supports multipart file upload
        with open(image_path, "rb") as f:
            files = {"image": f}
            # Explicitly request 75% quality and auto format to ensure size reduction
            data = {
                "quality": "75",
                "format": "auto"
            }
            response = requests.post(url, headers=headers, files=files, data=data, timeout=60)
        
        if response.status_code == 200:
            with open(image_path, "wb") as f:
                f.write(response.content)
            
            final_size_kb = os.path.getsize(image_path)/1024
            logger.info(f"API Success! Compressed size: {final_size_kb:.2f}KB")
            
            # If still over 1MB, we might need a more aggressive resize or pass
            if final_size_kb > 1000:
                logger.warning(f"File still large ({final_size_kb:.2f}KB). Re-compressing with lower quality...")
                with open(image_path, "rb") as f:
                    files = {"image": f}
                    data = {"quality": "50", "format": "jpg"}
                    response = requests.post(url, headers=headers, files=files, data=data, timeout=60)
                    if response.status_code == 200:
                        with open(image_path, "wb") as f:
                            f.write(response.content)
                        logger.info(f"Second pass success! Final size: {os.path.getsize(image_path)/1024:.2f}KB")
            
            return image_path
        else:
            logger.error(f"Compresto API failed with status {response.status_code}: {response.text}")
            return image_path
            
    except Exception as e:
        logger.error(f"Error during API compression: {str(e)}")
        return image_path

# ---------------- OCR.SPACE API HELPER ----------------
def ocr_space_file(filename, overlay=False, api_key=os.getenv("OCR_API_KEY"), language='eng'):
    """
    OCR.space API request with local file.
    :param filename: Your file path & name.
    :param overlay: Is OCR.space overlay required in your response.
                    Defaults to False.
    :param api_key: OCR.space API key.
                    Defaults to environment variable.
    :param language: Language code to be used in OCR.
                    List of available language codes can be found on https://ocr.space/OCRAPI
                    Defaults to 'eng'.
    :return: Resulting text.
    """
    payload = {
        'isOverlayRequired': overlay,
        'apikey': api_key,
        'language': language,
        'detectOrientation': 'true',
        'scale': 'true',
        'OCREngine': '2' # Engine 2 is better for some documents
    }
    with open(filename, 'rb') as f:
        r = requests.post('https://api.ocr.space/parse/image',
                          files={filename: f},
                          data=payload,
                          )
    
    result = r.json()
    if result.get('IsErroredOnProcessing'):
        raise Exception(f"OCR Error: {result.get('ErrorMessage')}")
    
    parsed_results = result.get('ParsedResults')
    if not parsed_results:
        return ""
    
    return parsed_results[0].get('ParsedText')

# ---------------- NAME / EMAIL / PHONE EXTRACT ----------------
def extract_details(text):
    logger.info(f"Raw OCR Text: \n{text}") # Print raw text for debugging
    
    name = "Not Found"
    email = "Not Found"
    phone = "Not Found"

    # Improved Regex Patterns
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    phone_pattern = r'^(?:(?:\+|00)[\s.-]{0,3})?(?:\d[\s.-]{0,3}){7,15}$'

    email_match = re.search(email_pattern, text)
    phone_match = re.search(phone_pattern, text)

    lines = [line.strip() for line in text.split("\n") if line.strip()]
    
    # Improved Name Heuristic
    # Most names don't have symbols or numbers
    name_blacklist = ["Phone", "Mobile", "Email", "Web", "Address", "Street", "Fax", "Direct"]
    
    for line in lines[:8]:
        # Filter noise
        if len(line) < 3: continue
        if "@" in line: continue
        if any(char.isdigit() for char in line): continue
        if any(word.lower() in line.lower() for word in name_blacklist): continue
        
        # Professional names often have 2-3 words
        words = line.split()
        if 2 <= len(words) <= 4:
            name = line
            break

    if email_match:
        email = email_match.group()

    if phone_match:
        # Basic cleanup for phone
        phone = phone_match.group().strip()

    return name, email, phone





# ---------------- ROUTES ----------------
@app.route("/", methods=["GET", "POST"])
def index():
    extracted_data = None

    if request.method == "POST":
        if 'image' not in request.files:
            flash("No file selected")
            return render_template("index.html", data=None)
            
        image = request.files["image"]
        if image.filename == '':
            flash("No file selected")
            return render_template("index.html", data=None)

        try:
            # Generate unique filename
            timestamp = int(time.time())
            filename = f"{timestamp}_{image.filename}"
            image_path = os.path.join(UPLOAD_FOLDER, filename)
            image.save(image_path)
            logger.info(f"Original image saved to {image_path}")

            # Compress for API compliance
            image_path = compress_image(image_path)

            # NEW: Use OCR.space API
            logger.info(f"Starting OCR with OCR.space for {image_path}")
            text = ocr_space_file(image_path)
            
            logger.info("OCR completed successfully")
            
            if not text or text.strip() == "":
                flash("OCR could not extract any text. Please try a clearer image.")
                return render_template("index.html", data=None)

            # Use the advanced extraction logic
            extracted_details = extract_business_card_details(text)
            
            extracted_data = extracted_details
            logger.info(f"Data extracted: {extracted_data}")
            flash("Scan successful! You can now edit the details below.")

        except Exception as e:
            logger.error(f"Error during OCR processing: {str(e)}")
            flash(f"Error processing image: {str(e)}")
            extracted_data = None

    return render_template("index.html", data=extracted_data)


@app.route("/save", methods=["POST"])
def save_data():
    try:
        # Get data from form
        data = {
            "Name": request.form.get("Name"),
            "Job Title": request.form.get("Job Title"),
            "Company": request.form.get("Company"),
            "Email": request.form.get("Email"),
            "Phone": request.form.get("Phone"),
            "Address": request.form.get("Address"),
            "Website": request.form.get("Website"),
            "Timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }

        # Save to MongoDB
        collection.insert_one(data)
        
        flash("Data saved to MongoDB successfully!")
        return render_template("index.html", data=None)
        
    except Exception as e:
        flash(f"Error saving data: {str(e)}")
        return render_template("index.html", data=None)

@app.route("/view_data")
def view_data():
    try:
        # Fetch all records from MongoDB
        records = list(collection.find())
        # Convert ObjectId to string for JSON serialization in template
        for r in records:
            r['_id'] = str(r['_id'])
        return render_template("view_data.html", records=records)
    except Exception as e:
        flash(f"Error fetching data: {str(e)}")
        return render_template("index.html", data=None)

@app.route("/export_excel")
def export_excel():
    try:
        # Fetch data
        records = list(collection.find())
        
        if not records:
             flash("No data to export")
             return render_template("view_data.html", records=[])

        # Convert to DataFrame
        df = pd.DataFrame(records)
        
        # Drop _id column if exists
        if "_id" in df.columns:
            df = df.drop(columns=["_id"])
            
        # Create Excel file in memory
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Sheet1')
        output.seek(0)
        
        return send_file(output, download_name="business_cards.xlsx", as_attachment=True)

    except Exception as e:
        logger.error(f"Export failed: {e}")
        flash(f"Error exporting data: {str(e)}")
        return render_template("view_data.html", records=list(collection.find()))

@app.route("/edit/<id>", methods=["POST"])
def edit_record(id):
    try:
        # Get form data
        updated_data = {
            "Name": request.form.get("Name"),
            "Job Title": request.form.get("Job Title"),
            "Company": request.form.get("Company"),
            "Email": request.form.get("Email"),
            "Phone": request.form.get("Phone"),
            "Address": request.form.get("Address"),
            "Website": request.form.get("Website"),
            "Timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Update in MongoDB
        collection.update_one({"_id": ObjectId(id)}, {"$set": updated_data})
        flash("Record updated successfully!")
        
    except Exception as e:
        logger.error(f"Edit failed: {e}")
        flash(f"Error updating record: {str(e)}")
    
    return redirect(url_for('view_data'))

@app.route("/delete/<id>")
def delete_record(id):
    try:
        # Delete from MongoDB
        collection.delete_one({"_id": ObjectId(id)})
        flash("Record deleted successfully!")
        
    except Exception as e:
        logger.error(f"Delete failed: {e}")
        flash(f"Error deleting record: {str(e)}")
    
    return redirect(url_for('view_data'))



if __name__ == "__main__":
    # Run on all interfaces with port from environment variable (Render compatibility)
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

