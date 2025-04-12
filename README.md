# My Journal

A Flask-based web application for managing personal journals.

## Features

- User authentication (login/register)
- MongoDB database integration
- Responsive web design

## Installation

1. Clone the repository:
```
git clone https://github.com/yourusername/my-journal.git
cd my-journal
```

2. Create and activate a virtual environment:
```
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install the dependencies:
```
pip install -r requirements.txt
```

4. Create a `.env` file in the root directory with the following content:
```
MONGODB_HOST=your_mongodb_connection_string
```

5. Run the application:
```
cd Journal
flask run
```

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
