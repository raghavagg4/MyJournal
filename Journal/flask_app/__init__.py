# 3rd-party packages
from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from flask_mongoengine import MongoEngine
from flask_login import (
    LoginManager,
    current_user,
    login_user,
    logout_user,
    login_required,
)
from flask_bcrypt import Bcrypt
from werkzeug.utils import secure_filename
import logging
from pymongo.errors import NetworkTimeout, ConnectionFailure
import time
import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

db = MongoEngine()
login_manager = LoginManager()
bcrypt = Bcrypt()

from .users.routes import users
from .ai.routes import ai
from .routes import main

def custom_404(e):
    return render_template("404.html"), 404

def custom_500(e):
    return render_template("500.html"), 500

def create_app(test_config=None):
    app = Flask(__name__,
                static_folder='static',
                static_url_path='/static')

    # Configure logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    app.config.from_pyfile("config.py", silent=False)
    if test_config is not None:
        app.config.update(test_config)

    # Check Gemini API key
    gemini_api_key = os.getenv('GEMINI_API_KEY')
    if not gemini_api_key or gemini_api_key == 'your_gemini_api_key_here':
        logger.error("GEMINI_API_KEY is not set or is using the default value. Please set a valid API key in your .env file.")
    else:
        try:
            genai.configure(api_key=gemini_api_key)
            # Use gemini-1.5-pro model
            model = genai.GenerativeModel('gemini-1.5-pro')
            response = model.generate_content("Test connection")
            logger.info("Gemini API connection successful")
        except Exception as e:
            logger.error(f"Gemini API connection failed: {str(e)}")

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)

    # Register blueprints
    app.register_blueprint(users)
    app.register_blueprint(ai)
    app.register_blueprint(main)

    # Register error handlers
    app.register_error_handler(404, custom_404)
    app.register_error_handler(500, custom_500)

    login_manager.login_view = "users.login"

    # Favicon route
    @app.route('/favicon.ico')
    def favicon():
        return send_from_directory(
            os.path.join(app.root_path, 'static'),
            'favicon.ico',
            mimetype='image/vnd.microsoft.icon'
        )

    # MongoDB connection retry logic
    with app.app_context():
        max_retries = 3
        retry_delay = 1  # seconds

        for attempt in range(max_retries):
            try:
                # Test MongoDB connection
                db.connection.server_info()
                logger.info("MongoDB connection successful")
                break
            except (NetworkTimeout, ConnectionFailure) as e:
                logger.warning(f"Attempting to connect to MongoDB (attempt {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                else:
                    logger.error(f"Failed to connect to MongoDB after multiple attempts: {str(e)}")
                    # Continue without breaking, as the app might work with partial functionality
                    logger.warning("Continuing without MongoDB connection. Some features may not work.")

    return app
