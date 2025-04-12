from flask_login import UserMixin
from datetime import datetime, timezone
from . import db, login_manager
from werkzeug.security import generate_password_hash, check_password_hash
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import os

# Salt for encryption (should be stored securely in production)
ENCRYPTION_SALT = os.environ.get('ENCRYPTION_SALT', os.urandom(16))
if isinstance(ENCRYPTION_SALT, str):
    ENCRYPTION_SALT = ENCRYPTION_SALT.encode()

@login_manager.user_loader
def load_user(user_id):
    try:
        return User.objects(username=user_id).first()
    except:
        return None

class User(db.Document, UserMixin):
    username = db.StringField(required=True, unique=True, min_length=1, max_length=40)
    email = db.EmailField(required=True, unique=True)
    password = db.StringField(required=True)

    meta = {
        'indexes': [
            'username',
            'email'
        ]
    }

    # Returns unique string identifying our object
    def get_id(self):
        return self.username

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

class JournalEntry(db.Document):
    user = db.ReferenceField(User, required=True)
    title = db.StringField(required=True, max_length=100)
    content = db.StringField(required=True)  # This will store encrypted content
    created_at = db.DateTimeField(default=datetime.now)
    updated_at = db.DateTimeField(default=datetime.now)

    meta = {
        'ordering': ['-created_at'],
        'indexes': [
            'user',
            'created_at',
            {'fields': ['user', 'created_at']}  # Compound index for user-specific queries
        ]
    }

    @staticmethod
    def _get_encryption_key(user_id):
        """Generate an encryption key based on user_id and salt"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=ENCRYPTION_SALT,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(user_id.encode()))
        return key

    @classmethod
    def encrypt_content(cls, content, user_id):
        """Encrypt the journal entry content"""
        key = cls._get_encryption_key(user_id)
        cipher = Fernet(key)
        encrypted_content = cipher.encrypt(content.encode())
        return encrypted_content.decode()

    def decrypt_content(self):
        """Decrypt the journal entry content"""
        key = self._get_encryption_key(str(self.user.id))
        cipher = Fernet(key)
        decrypted_content = cipher.decrypt(self.content.encode())
        return decrypted_content.decode()

