from flask import Flask, request, jsonify, render_template
from werkzeug.utils import secure_filename
from pdf2image import convert_from_path
import pytesseract
import os
from PIL import Image
import re

# Initialize the Flask app
app = Flask(__name__)

# Configure upload and output folders
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
POPPLER_PATH = r"C:\Users\ASHAPURNA\Downloads\Release-24.08.0-0\poppler-24.08.0\Library\bin"
TESSERACT_CMD = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER

# Ensure folders exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

import os

import os
POPPLER_PATH = os.getenv("POPPLER_PATH", "/app/poppler-23.11.0/bin")

images = convert_from_path("your_pdf_file.pdf", poppler_path=POPPLER_PATH)

# Configure Tesseract
pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD

# Allowed extensions for file upload
ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_structured_data(raw_text):
    """
    Parse the raw text and extract key fields like Name, DOB, Address, and Aadhaar No.
    """
    structured_data = {
        "Name": None,
        "DOB": None,
        "Address": None,
        "Aadhaar No.": None
    }
    
    lines = raw_text.split("\n")
    for line in lines:
        line = line.strip()
        
        # Extract Name
        name_match = re.search(r'(?i)(name\s*[:\-]\s*)([A-Za-z\s]+)', line)
        if name_match:
            structured_data["Name"] = name_match.group(2).strip()
        
        # Extract DOB
        dob_match = re.search(r'(?i)(dob|date of birth)\s*[:\-]\s*(\d{2}/\d{2}/\d{4})', line)
        if dob_match:
            structured_data["DOB"] = dob_match.group(2).strip()
        
        # Extract Address
        if "address" in line.lower():
            structured_data["Address"] = line.split(":")[-1].strip()
        
        # Extract Aadhaar Number (Assuming a 12-digit number format)
        aadhaar_match = re.search(r'\b\d{4}\s?\d{4}\s?\d{4}\b', line)
        if aadhaar_match:
            structured_data["Aadhaar No."] = aadhaar_match.group().replace(" ", "").strip()
    
    return structured_data

# Home route
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"success": False, "error": "No file part in the request"})

    file = request.files['file']

    if file.filename == '':
        return jsonify({"success": False, "error": "No file selected"})

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        try:
            extracted_text = ""
            if filename.lower().endswith('.pdf'):
                images = convert_from_path(file_path, poppler_path=POPPLER_PATH)
                for i, image in enumerate(images):
                    output_file = os.path.join(app.config['OUTPUT_FOLDER'], f"{filename}_page_{i + 1}.jpg")
                    image.save(output_file, "JPEG")
                    text = pytesseract.image_to_string(image)
                    extracted_text += f"--- Page {i + 1} ---\n{text}\n"
            else:
                image = Image.open(file_path)
                extracted_text = pytesseract.image_to_string(image)

            # Extract structured data
            structured_data = extract_structured_data(extracted_text)

            if not extracted_text.strip():
                return jsonify({"success": False, "error": "OCR failed. No text extracted."})

            return jsonify({"success": True, "structured_data": structured_data, "text": extracted_text})

        except Exception as e:
            return jsonify({"success": False, "error": f"Error processing file: {e}"})
    else:
        return jsonify({"success": False, "error": "Invalid file type"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)

