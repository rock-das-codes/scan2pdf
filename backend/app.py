from flask import Flask, request, jsonify
from flask_cors import CORS
import pytesseract
import cv2 
import os
import re
import traceback
import logging
import subprocess
import sys
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
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff', 'webp'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def check_and_configure_tesseract():
    """Check if Tesseract is available and configure it properly"""
    try:
        # First try to run tesseract command to check if it's available
        result = subprocess.run(['tesseract', '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            logger.info(f"Tesseract found: {result.stdout.split()[1] if result.stdout.split() else 'unknown version'}")
            return True
    except FileNotFoundError:
        logger.error("Tesseract command not found in PATH")
    except subprocess.TimeoutExpired:
        logger.error("Tesseract command timed out")
    except Exception as e:
        logger.error(f"Error checking Tesseract: {str(e)}")
    
    # Try common installation paths
    possible_paths = [
        '/usr/bin/tesseract',
        '/usr/local/bin/tesseract',
        '/opt/homebrew/bin/tesseract',
        '/usr/share/tesseract-ocr/4.00/tessdata',
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            try:
                if path.endswith('tesseract'):
                    pytesseract.pytesseract.tesseract_cmd = path
                    # Test if it works
                    result = subprocess.run([path, '--version'], 
                                          capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        logger.info(f"Tesseract configured at: {path}")
                        return True
            except Exception as e:
                logger.debug(f"Failed to configure Tesseract at {path}: {e}")
                continue
    
    return False

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
        tesseract_status = check_and_configure_tesseract()
        return jsonify({
            "message": "OCR API is running!", 
            "status": "healthy",
            "tesseract_available": tesseract_status
        })
    except Exception as e:
        logger.error(f"Error in hello route: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/health')
def health():
    try:
        # Test imports
        import cv2
        import pytesseract
        
        # Check Tesseract availability
        tesseract_available = check_and_configure_tesseract()
        
        return jsonify({
            "status": "healthy" if tesseract_available else "partial",
            "opencv_version": cv2.__version__,
            "tesseract_available": tesseract_available,
            "upload_folder_exists": os.path.exists(UPLOAD_FOLDER),
            "tesseract_cmd": pytesseract.pytesseract.tesseract_cmd if tesseract_available else "Not found"
        }), 200
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            "status": "unhealthy", 
            "error": str(e)
        }), 500

@app.route("/ocr", methods=["POST"])
def extract_text():
    filepath = None
    try:
        # Create upload folder
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        logger.info("Upload folder created/verified")
        
        # Check and configure Tesseract
        if not check_and_configure_tesseract():
            logger.error("Tesseract not found or not configured properly")
            return jsonify({
                "error": "Tesseract OCR not available on server",
                "details": "Please ensure tesseract-ocr is installed: sudo apt-get install tesseract-ocr tesseract-ocr-eng"
            }), 500
        
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
            return jsonify({"error": "Invalid file type. Allowed: png, jpg, jpeg, gif, bmp, tiff, webp"}), 400

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
            if os.path.exists(filepath):
                os.remove(filepath)  # Clean up
            return jsonify({"error": "Invalid image file or corrupted"}), 400

        # Convert to grayscale
        logger.info("Converting to grayscale")
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Apply image preprocessing for better OCR results
        logger.info("Applying image preprocessing")
        # Remove noise
        gray = cv2.medianBlur(gray, 3)
        
        # Apply threshold to get better contrast
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # Use Tesseract for OCR with custom configuration
        logger.info("Starting OCR with Tesseract")
        
        # OCR Engine Mode 3, Page Segmentation Mode 6 for better results
        custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz .,!?;:()-'
        
        try:
            ocr_data = pytesseract.image_to_data(thresh, output_type=pytesseract.Output.DICT, config=custom_config)
            logger.info("OCR completed successfully")
        except Exception as ocr_error:
            logger.error(f"OCR processing failed: {ocr_error}")
            # Try with simpler configuration as fallback
            logger.info("Trying OCR with simpler configuration")
            ocr_data = pytesseract.image_to_data(thresh, output_type=pytesseract.Output.DICT)

        # Build cleaned lines of text
        lines = []
        current_line_num = -1
        line_text = ""

        for i in range(len(ocr_data['text'])):
            word = ocr_data['text'][i].strip()
            confidence = int(ocr_data['conf'][i]) if ocr_data['conf'][i] != '-1' else 0
            
            # Skip words with very low confidence
            if not word or confidence < 30:
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

        # Clean junk characters and filter out very short or meaningless lines
        cleaned_lines = []
        for line in lines:
            # Remove non-ASCII characters but keep common punctuation
            cleaned_line = re.sub(r'[^\x20-\x7E]', '', line)
            # Remove lines that are too short or contain only punctuation
            if len(cleaned_line.strip()) > 2 and not re.match(r'^[^\w\s]+$', cleaned_line.strip()):
                cleaned_lines.append(cleaned_line.strip())
        
        # Clean up uploaded file
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                logger.info(f"Cleaned up file: {filepath}")
        except Exception as cleanup_error:
            logger.warning(f"Failed to cleanup file: {cleanup_error}")

        logger.info(f"OCR successful, extracted {len(cleaned_lines)} lines")
        return jsonify({
            "lines": cleaned_lines,
            "total_lines": len(cleaned_lines),
            "status": "success",
            "message": f"Successfully extracted {len(cleaned_lines)} lines of text"
        })

    except pytesseract.TesseractNotFoundError:
        logger.error("Tesseract not found")
        return jsonify({
            "error": "Tesseract OCR not found on server",
            "details": "Please install: sudo apt-get install tesseract-ocr tesseract-ocr-eng"
        }), 500
    except pytesseract.TesseractError as e:
        logger.error(f"Tesseract error: {e}")
        return jsonify({
            "error": f"OCR processing failed: {str(e)}",
            "details": "Tesseract encountered an error during processing"
        }), 500
    except Exception as e:
        logger.error(f"Unexpected error in OCR: {e}")
        logger.error(traceback.format_exc())
        
        # Try to cleanup file if it exists
        try:
            if filepath and os.path.exists(filepath):
                os.remove(filepath)
                logger.info("Cleaned up file after error")
        except Exception as cleanup_error:
            logger.warning(f"Failed to cleanup file after error: {cleanup_error}")
            
        return jsonify({
            "error": f"Processing failed: {str(e)}",
            "details": "An unexpected error occurred during image processing"
        }), 500

if __name__ == '__main__':
    # Test basic functionality on startup
    try:
        import cv2
        import pytesseract
        print(f"OpenCV version: {cv2.__version__}")
        
        # Check Tesseract availability
        if check_and_configure_tesseract():
            print("✅ Tesseract is available and configured")
        else:
            print("⚠️  Tesseract not found - OCR will not work")
            print("   Install with: sudo apt-get install tesseract-ocr tesseract-ocr-eng")
        
        print("Starting Flask app...")
    except Exception as e:
        print(f"Startup error: {e}")
    
    app.run(host='0.0.0.0', port=5000, debug=True)