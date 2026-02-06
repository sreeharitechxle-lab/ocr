import cv2
import pytesseract
import os
import sys

# Configure Tesseract
if os.name == 'nt':
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def run_test(image_path):
    print(f"Testing image: {image_path}")
    if not os.path.exists(image_path):
        print("File does not exist!")
        return

    img = cv2.imread(image_path)
    if img is None:
        print("Failed to load image via cv2.")
        return

    # Mode 1: Original
    print("\n--- MODE 1: ORIGINAL ---")
    try:
        text = pytesseract.image_to_string(img)
        print(text.strip())
    except Exception as e:
        print(f"Error: {e}")

    # Mode 2: Gray
    print("\n--- MODE 2: GRAYSCALE ---")
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    try:
        text = pytesseract.image_to_string(gray)
        print(text.strip())
    except Exception as e:
        print(f"Error: {e}")

    # Mode 3: Threshold (App Logic)
    print("\n--- MODE 3: THRESHOLD (App Logic) ---")
    gray_resized = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    thresh = cv2.threshold(gray_resized, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    try:
        text = pytesseract.image_to_string(thresh, config='--oem 3 --psm 4') # App uses psm 4
        print(text.strip())
    except Exception as e:
        print(f"Error: {e}")

    # Mode 4: Threshold with PSM 6 (Block of text)
    print("\n--- MODE 4: THRESHOLD (PSM 6) ---")
    try:
        text = pytesseract.image_to_string(thresh, config='--oem 3 --psm 6')
        print(text.strip())
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    path = "test_image.png"
    if len(sys.argv) > 1:
        path = sys.argv[1]
    run_test(path)
