import os
from flask import Flask, request, send_file, jsonify
import logging
from xls_processor import process_xls
from config_loader import load_config

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CONFIG_PATH = "config.yaml"
TEMP_DIR = "temp"
TEST_MODE = os.getenv("TEST_MODE", "False").lower() == "true"

os.makedirs(TEMP_DIR, exist_ok=True)

@app.route('/upload', methods=['POST'])
def upload_xls():
    try:
        if 'file' not in request.files:
            logger.error("No file part in request")
            return jsonify({"error": "No file part"}), 400
        file = request.files['file']
        if file.filename == '':
            logger.error("No selected file")
            return jsonify({"error": "No selected file"}), 400
        if not file.filename.endswith(('.xlsx', '.xls')):
            logger.error("File is not an XLS or XLSX")
            return jsonify({"error": "File must be an XLS or XLSX"}), 400

        xls_path = os.path.join(TEMP_DIR, "temp.xlsx")
        file.save(xls_path)
        logger.info(f"XLS saved temporarily: {xls_path}")

        config = load_config(CONFIG_PATH)

        output_file = process_xls(xls_path, config, TEMP_DIR, TEST_MODE)

        if os.path.exists(xls_path):
            os.remove(xls_path)
            logger.info(f"Temporary XLS deleted: {xls_path}")

        if output_file and os.path.exists(output_file):
            return send_file(output_file, mimetype='image/png', as_attachment=True, download_name='label.png')
        else:
            return jsonify({"error": "Failed to process XLS or generate label"}), 500

    except Exception as e:
        logger.error(f"Error in upload endpoint: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
