import os
from flask import Flask, request, send_file, jsonify
import logging
from pdf_processor import process_pdf
from config_loader import load_config

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CONFIG_PATH = "/app/config.yaml"
TEMP_DIR = "/app/temp"
TEST_MODE = os.getenv("TEST_MODE", "False").lower() == "true"

os.makedirs(TEMP_DIR, exist_ok=True)

@app.route('/upload', methods=['POST'])
def upload_pdf():
    try:
        if 'file' not in request.files:
            logger.error("No file part in request")
            return jsonify({"error": "No file part"}), 400
        file = request.files['file']
        if file.filename == '':
            logger.error("No selected file")
            return jsonify({"error": "No selected file"}), 400
        if not file.filename.endswith('.pdf'):
            logger.error("File is not a PDF")
            return jsonify({"error": "File must be a PDF"}), 400

        pdf_path = os.path.join(TEMP_DIR, "temp.pdf")
        file.save(pdf_path)
        logger.info(f"PDF saved temporarily: {pdf_path}")

        config = load_config(CONFIG_PATH)

        output_file = process_pdf(pdf_path, config, TEMP_DIR, TEST_MODE)

        if os.path.exists(pdf_path):
            os.remove(pdf_path)
            logger.info(f"Temporary PDF deleted: {pdf_path}")

        if output_file and os.path.exists(output_file):
            return send_file(output_file, mimetype='image/png', as_attachment=True, download_name='label.png')
        else:
            return jsonify({"error": "Failed to process PDF or generate label"}), 500

    except Exception as e:
        logger.error(f"Error in upload endpoint: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
