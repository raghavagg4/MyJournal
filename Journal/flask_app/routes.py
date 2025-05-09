# Remove the Gemini API route and its imports

from flask import Blueprint, current_app, send_from_directory
import os

main = Blueprint('main', __name__)

@main.route('/debug-static')
def debug_static():
    """Debug route to list static files"""
    static_folder = current_app.static_folder
    files = os.listdir(static_folder)
    return {"static_folder": static_folder, "files": files}
