import os
import certifi
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

SECRET_KEY = os.getenv('SECRET_KEY', os.urandom(24))
MONGODB_HOST = os.getenv('MONGODB_HOST')
MONGODB_SETTINGS = {
    'host': MONGODB_HOST,
    'tlsCAFile': certifi.where(),
    'connectTimeoutMS': 30000,
    'socketTimeoutMS': 30000,
    'serverSelectionTimeoutMS': 30000
}
