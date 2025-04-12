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


# stdlib
from datetime import datetime
import os

db = MongoEngine()
login_manager = LoginManager()
bcrypt = Bcrypt()

from .users.routes import users

def custom_404(e):
    return render_template("404.html"), 404

def custom_500(e):
    return render_template("500.html"), 500

def create_app(test_config=None):
    app = Flask(__name__)

    # Configure logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    app.config.from_pyfile("config.py", silent=False)
    if test_config is not None:
        app.config.update(test_config)

    # Initialize MongoDB with retry logic
    max_retries = 3
    retry_delay = 2  # seconds

    for attempt in range(max_retries):
        try:
            logger.info(f"Attempting to connect to MongoDB (attempt {attempt+1}/{max_retries})")
            db.init_app(app)
            # Test the connection
            with app.app_context():
                db.connection.server_info()
            logger.info("MongoDB connection successful")
            break
        except (NetworkTimeout, ConnectionFailure) as e:
            if attempt < max_retries - 1:
                logger.warning(f"MongoDB connection failed: {str(e)}. Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                logger.error(f"MongoDB connection failed after {max_retries} attempts: {str(e)}")
                # Continue without breaking, as the app might work with partial functionality

    login_manager.init_app(app)
    bcrypt.init_app(app)

    app.register_blueprint(users)
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

    return app
