from flask import Flask

def create_app():
    app = Flask(__name__)
    from .routes import setup_routes
    setup_routes(app)
    return app