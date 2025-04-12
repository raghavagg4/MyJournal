# Personal Journal Application

A secure journal application where users can write and save encrypted journal entries.

## Features

- User registration and authentication
- Encrypted journal entries using Fernet symmetric encryption
- Create, view, and delete journal entries
- All entries are stored in MongoDB

## Setup Instructions

1. Clone the repository
2. Set up a virtual environment:
   ```
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install the dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Set environment variables (optional):
   ```
   export ENCRYPTION_SALT=your_custom_salt  # For production
   ```
5. Run the application:
   ```
   export FLASK_APP=Journal/flask_app:create_app
   export FLASK_ENV=development  # For development mode
   flask run
   ```

## Security Features

- User passwords are hashed with bcrypt
- Journal entries are encrypted with Fernet symmetric encryption
- Each user's entries are encrypted with a unique key derived from their user ID
- All sensitive data is stored in encrypted form in the database

## Development

To set up a development environment:

1. Follow the setup steps above
2. Activate the virtual environment
3. Run the application in debug mode

## Required Dependencies

- Flask
- MongoEngine (MongoDB ODM)
- Flask-Login for authentication
- Flask-WTF for forms
- Cryptography for secure encryption

## Technologies Used

- Flask
- MongoDB with Flask-MongoEngine
- Flask-Login for user authentication
- Bootstrap for styling

## Project Structure

- `flask_app/`: Main application package
  - `templates/`: HTML templates
  - `static/`: CSS, JavaScript, and other static files
  - `config.py`: Configuration settings
  - `__init__.py`: Application factory
  - `models.py`: Database models
  - `forms.py`: Form definitions
  - `users/`: User authentication blueprint
- `run.py`: Application entry point
