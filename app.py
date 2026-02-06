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
import pytesseract
from PIL import Image

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = "supersecretkey"

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

UPLOAD_FOLDER = "uploads"

# MongoDB Configuration
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")

try:
    client = MongoClient(MONGO_URI)
    db = client["business_card_db"]
    collection = db["cards"]
    logger.info(f"Connected to MongoDB successfully")
except Exception as e:
    logger.error(f"Failed to connect to MongoDB: {e}")
    client = None
    collection = None

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def compress_image(image_path):
    """Compress image using PIL for basic compression"""
    try:
        with Image.open(image_path) as img:
            # Convert to RGB if necessary
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            
            # Resize if too large
            max_size = (1200, 1200)
            if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Save with compression
            img.save(image_path, 'JPEG', quality=85, optimize=True)
            
        final_size_kb = os.path.getsize(image_path)/1024
        logger.info(f"Image compressed to {final_size_kb:.2f}KB")
        return image_path
        
    except Exception as e:
        logger.error(f"Error compressing image: {str(e)}")
        return image_path

def extract_text_from_image(image_path):
    """Extract text from image using Tesseract OCR"""
    try:
        with Image.open(image_path) as img:
            # Convert to grayscale for better OCR
            if img.mode != 'L':
                img = img.convert('L')
            
            # Extract text
            text = pytesseract.image_to_string(img)
            return text.strip()
            
    except Exception as e:
        logger.error(f"Error extracting text: {str(e)}")
        return ""

def extract_business_card_details(text):
    """Extract business card details from OCR text"""
    details = {
        "Name": "Not Found",
        "Job Title": "Not Found",
        "Company": "Not Found",
        "Email": "Not Found",
        "Phone": "Not Found",
        "Address": "Not Found",
        "Website": "Not Found"
    }

    if not text:
        return details

    lines = [line.strip() for line in text.split('\n') if line.strip()]
    if not lines:
        return details

    # Regex patterns
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    url_pattern = r'(?:https?:\/\/|www\.)[a-zA-Z0-9-]+\.[a-zA-Z]{2,}(?:\/[^\s]*)?'
    phone_pattern = r'(?:(?:\+|00)[\s.-]{0,3})?(?:\d[\s.-]{0,3}){7,15}'

    # Extract email
    for line in lines:
        email_match = re.search(email_pattern, line)
        if email_match and details["Email"] == "Not Found":
            details["Email"] = email_match.group()

    # Extract website
    for line in lines:
        url_match = re.search(url_pattern, line)
        if url_match and details["Website"] == "Not Found":
            details["Website"] = url_match.group()

    # Extract phone
    for line in lines:
        phone_match = re.search(phone_pattern, line)
        if phone_match and details["Phone"] == "Not Found":
            digits = re.sub(r'\D', '', phone_match.group())
            if len(digits) >= 8:
                details["Phone"] = phone_match.group().strip()

    # Extract name and job title
    job_keywords = ["Manager", "Director", "Chief", "Lead", "Head", "Consultant", "Engineer", "Developer", "Designer", "Sales", "Executive", "CEO", "CTO", "Founder", "President"]
    
    name_found = False
    job_found = False
    
    for i, line in enumerate(lines[:10]):  # Check first 10 lines
        if not name_found and len(line) > 3 and len(line.split()) <= 4:
            if not any(char.isdigit() for char in line) and '@' not in line:
                if not any(word.lower() in line.lower() for word in ["phone", "email", "address", "web", "www"]):
                    details["Name"] = line
                    name_found = True
        
        if not job_found and any(keyword.lower() in line.lower() for keyword in job_keywords):
            details["Job Title"] = line
            job_found = True

    # Extract company
    company_suffixes = ["inc", "ltd", "llc", "corp", "limited", "pvt ltd", "private limited", "group", "solutions", "global", "systems", "technologies", "company"]
    
    for line in lines:
        if any(suffix in line.lower() for suffix in company_suffixes):
            details["Company"] = line
            break

    # Extract address (simplified)
    address_keywords = ["st.", "road", "rd.", "ave", "lane", "suite", "floor", "block", "sector", "hwy", "bldg", "plot"]
    address_parts = []
    
    for line in lines:
        if any(keyword in line.lower() for keyword in address_keywords) or re.search(r'\b\d{5,6}\b', line):
            address_parts.append(line)
    
    if address_parts:
        details["Address"] = ", ".join(address_parts[:3])  # Limit to 3 lines

    return details

# Routes
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
            logger.info(f"Image saved to {image_path}")

            # Compress image
            image_path = compress_image(image_path)

            # Extract text using Tesseract
            logger.info(f"Starting OCR for {image_path}")
            text = extract_text_from_image(image_path)
            
            logger.info("OCR completed successfully")
            
            if not text or text.strip() == "":
                flash("OCR could not extract any text. Please try a clearer image.")
                return render_template("index.html", data=None)

            # Extract business card details
            extracted_details = extract_business_card_details(text)
            
            extracted_data = extracted_details
            logger.info(f"Data extracted: {extracted_data}")
            flash("Scan successful! You can now edit the details below.")

        except Exception as e:
            logger.error(f"Error during processing: {str(e)}")
            flash(f"Error processing image: {str(e)}")
            extracted_data = None

    return render_template("index.html", data=extracted_data)

@app.route("/save", methods=["POST"])
def save_data():
    if collection is None:
        flash("Database not available")
        return render_template("index.html", data=None)
        
    try:
        data = {
            "Name": request.form.get("Name", "Not Found"),
            "Job Title": request.form.get("Job Title", "Not Found"),
            "Company": request.form.get("Company", "Not Found"),
            "Email": request.form.get("Email", "Not Found"),
            "Phone": request.form.get("Phone", "Not Found"),
            "Address": request.form.get("Address", "Not Found"),
            "Website": request.form.get("Website", "Not Found"),
            "Timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }

        collection.insert_one(data)
        flash("Data saved successfully!")
        return render_template("index.html", data=None)
        
    except Exception as e:
        flash(f"Error saving data: {str(e)}")
        return render_template("index.html", data=None)

@app.route("/view_data")
def view_data():
    if collection is None:
        flash("Database not available")
        return render_template("index.html", data=None)
        
    try:
        records = list(collection.find())
        for r in records:
            r['_id'] = str(r['_id'])
        return render_template("view_data.html", records=records)
    except Exception as e:
        flash(f"Error fetching data: {str(e)}")
        return render_template("index.html", data=None)

@app.route("/export_excel")
def export_excel():
    if collection is None:
        flash("Database not available")
        return render_template("view_data.html", records=[])
        
    try:
        records = list(collection.find())
        
        if not records:
            flash("No data to export")
            return render_template("view_data.html", records=[])

        df = pd.DataFrame(records)
        
        if "_id" in df.columns:
            df = df.drop(columns=["_id"])
            
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
    if collection is None:
        flash("Database not available")
        return redirect(url_for('view_data'))
        
    try:
        updated_data = {
            "Name": request.form.get("Name", "Not Found"),
            "Job Title": request.form.get("Job Title", "Not Found"),
            "Company": request.form.get("Company", "Not Found"),
            "Email": request.form.get("Email", "Not Found"),
            "Phone": request.form.get("Phone", "Not Found"),
            "Address": request.form.get("Address", "Not Found"),
            "Website": request.form.get("Website", "Not Found"),
            "Timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        collection.update_one({"_id": ObjectId(id)}, {"$set": updated_data})
        flash("Record updated successfully!")
        
    except Exception as e:
        logger.error(f"Edit failed: {e}")
        flash(f"Error updating record: {str(e)}")
    
    return redirect(url_for('view_data'))

@app.route("/delete/<id>")
def delete_record(id):
    if collection is None:
        flash("Database not available")
        return redirect(url_for('view_data'))
        
    try:
        collection.delete_one({"_id": ObjectId(id)})
        flash("Record deleted successfully!")
        
    except Exception as e:
        logger.error(f"Delete failed: {e}")
        flash(f"Error deleting record: {str(e)}")
    
    return redirect(url_for('view_data'))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
