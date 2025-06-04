from flask import Flask, request, jsonify
from flask_cors import CORS
import pytesseract
import cv2 
import os
import re
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)
UPLOAD_FOLDER = "uploads"


@app.route("/ocr", methods=["POST"])
def extract_text():
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    if "image" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["image"]
    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    # Load image and preprocess
    img = cv2.imread(filepath)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Use Tesseract image_to_data for structured text
    ocr_data = pytesseract.image_to_data(gray, output_type=pytesseract.Output.DICT)

    # Build cleaned lines of text
    lines = []
    current_line_num = -1
    line_text = ""

    for i in range(len(ocr_data['text'])):
        word = ocr_data['text'][i].strip()
        if not word:
            continue

        line_num = ocr_data['line_num'][i]
        if line_num != current_line_num:
            if line_text:
                lines.append(line_text.strip())
            line_text = word
            current_line_num = line_num
        else:
            line_text += " " + word

    if line_text:
        lines.append(line_text.strip())

    # Clean junk characters
    cleaned_lines = [re.sub(r'[^\x00-\x7F]+', '', line) for line in lines]

    os.remove(filepath)

    return jsonify({ "lines": cleaned_lines })

if __name__ == "__main__":
    app.run(debug=True)
