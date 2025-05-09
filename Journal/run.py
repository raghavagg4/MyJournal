import os
import sys

# Add the current directory to the path so Python can find the flask_app module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask_app import create_app

app = create_app()

# This is needed for Vercel
if __name__ == '__main__':
    app.run(debug=True)
