from flask import Flask, request, jsonify
import io
from config import load_config, PRINTER_MODEL, USB_PATH
from pdf_handler import process_pdf

app = Flask(__name__)

@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400

        if file and file.filename.endswith('.pdf'):
            pdf_file = io.BytesIO(file.read())
            config = load_config()
            # Předáváme test_mode=True pro testovací režim
            success = process_pdf(pdf_file, config, PRINTER_MODEL, USB_PATH, test_mode=True)
            if success:
                return jsonify({'message': 'File processing started in test mode'}), 202
            else:
                return jsonify({'error': 'Failed to process file'}), 500
        else:
            return jsonify({'error': 'Invalid file type'}), 400

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
