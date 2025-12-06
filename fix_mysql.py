from app import app, db
from sqlalchemy import text

# Create the application context
with app.app_context():
    print("--- STARTING DATABASE REPAIR ---")

    # List of columns to add
    commands = [
        # Admin Table Updates
        "ALTER TABLE admin ADD COLUMN email VARCHAR(100) UNIQUE DEFAULT NULL",
        "ALTER TABLE admin ADD COLUMN contact_no VARCHAR(15) DEFAULT NULL",
        "ALTER TABLE admin ADD COLUMN profile_image VARCHAR(255) NOT NULL DEFAULT 'default.png'",
        
        # Staff Table Updates
        "ALTER TABLE staff ADD COLUMN profile_image VARCHAR(255) NOT NULL DEFAULT 'default.png'",
        
        # HOD Table Updates
        "ALTER TABLE hod ADD COLUMN profile_image VARCHAR(255) NOT NULL DEFAULT 'default.png'"
    ]

    for sql in commands:
        try:
            db.session.execute(text(sql))
            print(f"SUCCESS: {sql}")
        except Exception as e:
            # If error contains "Duplicate column", it means it is already fixed.
            if "Duplicate column" in str(e) or "1060" in str(e):
                print(f"SKIPPED (Already exists): {sql}")
            else:
                print(f"ERROR: {str(e)}")

    # Commit the changes
    try:
        db.session.commit()
        print("--- DATABASE REPAIR COMPLETE ---")
    except Exception as e:
        print(f"Error saving changes: {e}")