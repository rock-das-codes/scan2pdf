from flask import Flask, request, jsonify
from flask_cors import CORS
from paddleocr import TableRecognitionPipelineV2

import cv2 
import os
from werkzeug.utils import secure_filename
import psutil
import threading
import logging

app = Flask(__name__)
CORS(app, 
     origins=["*"],
     methods=["GET", "POST", "PUT", "DELETE"],
     allow_headers=["Content-Type", "Authorization"]
)

UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff', 'webp'}



logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize pipeline globally
pipeline = TableRecognitionPipelineV2()


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.errorhandler(500)
def internal_server_error(error):
    return jsonify({"error": "Internal server error", "message": str(error)}), 500

@app.route('/')
def hello():
    return jsonify({"message": "Welcome to the OCR API"}), 200

def convert_table_result(result):
    """Convert table result to JSON serializable format."""
    return {
        'type': 'table',
        'html': result.html if hasattr(result, 'html') else None,
        'cells': result.cells if hasattr(result, 'cells') else None,
        'boxes': result.boxes.tolist() if hasattr(result, 'boxes') else None,
        'confidence': float(result.confidence) if hasattr(result, 'confidence') else None
    }

@app.route("/ocr", methods=["POST"])
def extract_table():
  

    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    if "image" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["image"]

    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "Invalid file type. Allowed: png, jpg, jpeg, gif, bmp, tiff, webp"}), 400

    filename = secure_filename(file.filename)
    if not filename:
        filename = "image.png"

    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    if not os.path.exists(filepath):
        return jsonify({"error": "File save failed"}), 500

    img = cv2.imread(filepath)
    if img is None:
        if os.path.exists(filepath):
            os.remove(filepath)
        return jsonify({"error": "Invalid image file or corrupted"}), 400

    try:
        output = pipeline.predict(img)
        tables = []
        
        # Save files to output directory
        os.makedirs("./output", exist_ok=True)
        for idx, res in enumerate(output):
            res.save_to_html(f"./output/table_{idx}.html")
            res.save_to_json(f"./output/table_{idx}.json")
            
            # Convert result to serializable format
            tables.append(convert_table_result(res))
            
        return jsonify({
            "tables": tables,
            "message": "Table extraction completed successfully",
        })
    except Exception as ocr_error:
        logger.error(f"Table extraction error: {str(ocr_error)}")
        return jsonify({"error": "Table extraction failed", "message": str(ocr_error)}), 500

if __name__ == '__main__':
    try:
        import cv2
        print(f"OpenCV version: {cv2.__version__}")
        print("Starting Flask app...")
        print("Pipeline initialized successfully.")
        app.run(host='0.0.0.0', port=5000, debug=False)
    except Exception as e:
        print(f"Startup error: {e}")