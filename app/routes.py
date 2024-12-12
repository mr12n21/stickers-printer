from flask import Blueprint, jsonify
from .smb_processor import process_smb_folder

routes = Blueprint('routes', __name__)

@routes.route('/process', methods=['POST'])
def process_folder():
    try:
        process_smb_folder()
        return jsonify({"message": "process complete"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def setup_routes(app):
    app.register_blueprint(routes)