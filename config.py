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

    # Other settings...
    FAST2SMS_API_KEY = os.environ.get('FAST2SMS_API_KEY')