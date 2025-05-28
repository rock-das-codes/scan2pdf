from flask import Flask, request, jsonify
from flask_cors import CORS
import pytesseract
import cv2 
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.route("/ocr", methods=["POST"])
def extract_text():
    if "image" not in request.files:
        return jsonify({"error": "No file part"}), 400
      
    file = request.files["image"]
    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath) 

    img = cv2.imread(filepath)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    text = pytesseract.image_to_string(gray)

    os.remove(filepath)

    return jsonify({"text": text})
    
if __name__ == "__main__":
    app.run(debug=False)