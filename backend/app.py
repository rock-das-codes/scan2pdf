from flask import Flask, request, jsonify
from flask_cors import CORS
import pytesseract
import cv2 
import os
import re
import traceback
import logging
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app, 
     origins=["*"],  # Allow all origins for development
     methods=["GET", "POST", "PUT", "DELETE"],
     allow_headers=["Content-Type", "Authorization"]
)

# Enable logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.errorhandler(500)
def internal_server_error(error):
    logger.error(f"Server Error: {error}")
    return jsonify({"error": "Internal server error", "message": str(error)}), 500

@app.errorhandler(Exception)
def handle_exception(e):
    logger.error(f"Unhandled Exception: {e}")
    logger.error(traceback.format_exc())
    return jsonify({"error": "An unexpected error occurred", "message": str(e)}), 500

@app.route('/')
def hello():
    try:
        return jsonify({"message": "OCR API is running!", "status": "healthy"})
    except Exception as e:
        logger.error(f"Error in hello route: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/health')
def health():
    try:
        # Test imports
        import cv2
        import pytesseract
        
        return jsonify({
            "status": "healthy",
            "opencv_version": cv2.__version__,
            "tesseract_available": True
        }), 200
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            "status": "unhealthy", 
            "error": str(e)
        }), 500

@app.route("/ocr", methods=["POST"])
def extract_text():
    try:
        # Create upload folder
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        logger.info("Upload folder created/verified")
        
        # Check if file is present
        if "image" not in request.files:
            logger.warning("No file part in request")
            return jsonify({"error": "No file part"}), 400

        file = request.files["image"]
        
        # Check if file is selected
        if file.filename == '':
            logger.warning("No file selected")
            return jsonify({"error": "No file selected"}), 400
        
        # Check file extension
        if not allowed_file(file.filename):
            logger.warning(f"Invalid file type: {file.filename}")
            return jsonify({"error": "Invalid file type. Allowed: png, jpg, jpeg, gif, bmp, tiff"}), 400

        # Save file
        filename = secure_filename(file.filename)
        if not filename:
            filename = "image.png"  # fallback filename
            
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        logger.info(f"File saved: {filepath}")

        # Check if file exists and is readable
        if not os.path.exists(filepath):
            logger.error(f"File not found after saving: {filepath}")
            return jsonify({"error": "File save failed"}), 500

        # Load and process image
        logger.info("Loading image with OpenCV")
        img = cv2.imread(filepath)
        
        if img is None:
            logger.error(f"Failed to load image: {filepath}")
            os.remove(filepath)  # Clean up
            return jsonify({"error": "Invalid image file or corrupted"}), 400

        # Convert to grayscale
        logger.info("Converting to grayscale")
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Use Tesseract for OCR
        logger.info("Starting OCR with Tesseract")
        ocr_data = pytesseract.image_to_data(gray, output_type=pytesseract.Output.DICT)
        logger.info("OCR completed")

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
        cleaned_lines = [re.sub(r'[^\x00-\x7F]+', '', line) for line in lines if line.strip()]
        
        # Clean up uploaded file
        try:
            os.remove(filepath)
            logger.info(f"Cleaned up file: {filepath}")
        except Exception as cleanup_error:
            logger.warning(f"Failed to cleanup file: {cleanup_error}")

        logger.info(f"OCR successful, extracted {len(cleaned_lines)} lines")
        return jsonify({
            "lines": cleaned_lines,
            "total_lines": len(cleaned_lines),
            "status": "success"
        })

    except pytesseract.TesseractNotFoundError:
        logger.error("Tesseract not found")
        return jsonify({"error": "Tesseract OCR not found on server"}), 500
    except pytesseract.TesseractError as e:
        logger.error(f"Tesseract error: {e}")
        return jsonify({"error": f"OCR processing failed: {str(e)}"}), 500
    except Exception as e:
        logger.error(f"Unexpected error in OCR: {e}")
        logger.error(traceback.format_exc())
        
        # Try to cleanup file if it exists
        try:
            if 'filepath' in locals() and os.path.exists(filepath):
                os.remove(filepath)
        except:
            pass
            
        return jsonify({"error": f"Processing failed: {str(e)}"}), 500

if __name__ == '__main__':
    # Test basic functionality on startup
    try:
        import cv2
        import pytesseract
        print(f"OpenCV version: {cv2.__version__}")
        print("Tesseract available")
        print("Starting Flask app...")
    except Exception as e:
        print(f"Startup error: {e}")
    
    app.run(host='0.0.0.0', port=5000, debug=True)