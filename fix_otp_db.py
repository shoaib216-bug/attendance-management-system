from app import app, db
from sqlalchemy import text

with app.app_context():
    print("--- ADDING OTP COLUMNS ---")
    
    tables = ['admin', 'staff', 'hod']
    
    for table in tables:
        try:
            db.session.execute(text(f"ALTER TABLE {table} ADD COLUMN otp_hash VARCHAR(255) DEFAULT NULL"))
            db.session.execute(text(f"ALTER TABLE {table} ADD COLUMN otp_expiry DATETIME DEFAULT NULL"))
            print(f"Updated {table} table.")
        except Exception as e:
            if "Duplicate column" in str(e) or "1060" in str(e):
                print(f"{table}: Columns already exist.")
            else:
                print(f"Error updating {table}: {e}")

    db.session.commit()
    print("--- DB FIX COMPLETE ---")