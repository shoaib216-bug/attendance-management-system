import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'a-default-secret-key'

    # =========================================================================
    # === WE ARE FORCING A CONNECTION TO A BRAND NEW DATABASE NAME ===
    # =========================================================================
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:password@localhost/attendance_management'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # =========================================================================

    TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
    TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
    TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER')