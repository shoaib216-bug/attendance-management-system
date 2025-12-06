import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'default-secret-key-shoaib'

    # Database Configuration (Smart Switch)
    render_db_url = os.environ.get('DATABASE_URL')
    if render_db_url:
        if render_db_url.startswith("postgres://"):
            SQLALCHEMY_DATABASE_URI = render_db_url.replace("postgres://", "postgresql://", 1)
        else:
            SQLALCHEMY_DATABASE_URI = render_db_url
    else:
        # Localhost MySQL
        SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:password@localhost/attendance_management'

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # === UPLOAD FOLDER CONFIGURATION ===
    # This gets the folder where app.py is located
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    
    # Define path: static/images/profiles
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'images', 'profiles')
    
    # Max upload size: 16 Megabytes
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024

    # Twilio (SMS) Configuration
    TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
    TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
    TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER')