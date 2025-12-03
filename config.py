import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'a-default-secret-key'

    # =========================================================================
    # === SMART DATABASE CONFIGURATION ===
    # This logic automatically switches databases based on where the code is running.
    # =========================================================================
    
    # 1. Check if we are on Render (Render provides a 'DATABASE_URL')
    render_db_url = os.environ.get('DATABASE_URL')

    if render_db_url:
        # --- WE ARE ON RENDER (PRODUCTION) ---
        # Fix Render's URL format because SQLAlchemy requires 'postgresql://'
        if render_db_url.startswith("postgres://"):
            SQLALCHEMY_DATABASE_URI = render_db_url.replace("postgres://", "postgresql://", 1)
        else:
            SQLALCHEMY_DATABASE_URI = render_db_url
    else:
        # --- WE ARE ON LOCALHOST (YOUR PC) ---
        # Use your existing MySQL connection
        SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:password@localhost/attendance_management'

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # =========================================================================
    # === TWILIO SETTINGS ===
    # =========================================================================
    TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
    TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
    TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER')