from flask import Flask, request, jsonify
import io
from config import load_config, PRINTER_MODEL, USB_PATH
from pdf_handler import process_pdf

app = Flask(__name__)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file and file.filename.endswith('.pdf'):
        pdf_file = io.BytesIO(file.read())
        config = load_config()
        success = process_pdf(pdf_file, config, PRINTER_MODEL, USB_PATH)
        if success:
            return jsonify({'message': 'File processing started, printing in progress'}), 202
        else:
            return jsonify({'error': 'Failed to process file'}), 500
    else:
        return jsonify({'error': 'Invalid file type'}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)