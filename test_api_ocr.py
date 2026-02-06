import requests
import os
from dotenv import load_dotenv

load_dotenv()

def test_ocr_api(image_path):
    api_key = os.getenv("OCR_API_KEY")
    if not api_key:
        print("Error: OCR_API_KEY not found in .env")
        return

    print(f"Testing OCR.space API with image: {image_path}")
    
    payload = {
        'apikey': api_key,
        'language': 'eng',
        'isOverlayRequired': False,
        'OCREngine': '2'
    }
    
    try:
        with open(image_path, 'rb') as f:
            r = requests.post('https://api.ocr.space/parse/image',
                              files={image_path: f},
                              data=payload)
        
        result = r.json()
        if result.get('IsErroredOnProcessing'):
            print(f"API Error: {result.get('ErrorMessage')}")
            return
            
        parsed_results = result.get('ParsedResults')
        if parsed_results:
            text = parsed_results[0].get('ParsedText')
            print("\nExtracted Text:")
            print("-" * 30)
            print(text)
            print("-" * 30)
            print("\nSuccess!")
        else:
            print("No text parsed from image.")
            
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    # Use existing test image
    test_image = "test_image.png"
    if os.path.exists(test_image):
        test_ocr_api(test_image)
    else:
        print(f"Test image {test_image} not found.")
