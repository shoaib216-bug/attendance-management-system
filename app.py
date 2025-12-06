import os
from datetime import timedelta
from flask import Flask, redirect, url_for, render_template # <--- Added render_template
from flask_login import LoginManager
from sqlalchemy import text
from config import Config

# Models & Routes
from models.models import db, Admin, Staff, HOD 
from routes.auth_routes import auth_bp
from routes.admin_routes import admin_bp
from routes.staff_routes import staff_bp
from routes.hod_routes import hod_bp 
from routes.public_routes import public_bp

app = Flask(__name__)
app.config.from_object(Config)

app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=15)

@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, post-check=0, pre-check=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.admin_login'

@app.context_processor
def inject_user_types():
    return dict(isinstance=isinstance, Admin=Admin, Staff=Staff, HOD=HOD)

@login_manager.user_loader
def load_user(user_id_string):
    try:
        user_type, user_id = user_id_string.split('-')
        user_id = int(user_id)
    except (ValueError, AttributeError): return None

    if user_type == 'admin': return Admin.query.get(user_id)
    elif user_type == 'staff': return Staff.query.get(user_id)
    elif user_type == 'hod': return HOD.query.get(user_id)
    return None

app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(staff_bp, url_prefix='/staff')
app.register_blueprint(hod_bp, url_prefix='/hod')
app.register_blueprint(public_bp, url_prefix='/view') 

# =========================================================
# === UPDATED INDEX ROUTE (WELCOME PAGE) ===
# =========================================================
@app.route('/')
def index():
    with app.app_context():
        # Safety check: Ensure at least one Admin exists.
        # If the database is empty, force registration.
        try:
            if Admin.query.first() is None:
                return redirect(url_for('auth.register_admin'))
        except:
            # If DB tables don't exist yet, ignore error (will be fixed by db.create_all)
            pass 
        
        # If Admin exists, show the Welcome Page (templates/index.html)
        return render_template('index.html')

@app.route('/healthz')
def health_check(): return "OK", 200

# ==========================================
# === MYSQL DB FIX ROUTE ===
# ==========================================
@app.route('/fix-local-db')
def fix_local_db():
    results = []
    # Helper function to run MySQL "ADD COLUMN" safely
    def add_col(query):
        try:
            db.session.execute(text(query))
            return "Added"
        except Exception as e:
            # Error 1060 is "Duplicate column name" in MySQL
            if "1060" in str(e) or "Duplicate column" in str(e):
                return "Already Exists"
            return f"Error: {str(e)}"

    # 1. Admin Cols
    results.append("Admin Email: " + add_col("ALTER TABLE admin ADD email VARCHAR(100) UNIQUE DEFAULT NULL"))
    results.append("Admin Contact: " + add_col("ALTER TABLE admin ADD contact_no VARCHAR(15) DEFAULT NULL"))
    results.append("Admin Profile: " + add_col("ALTER TABLE admin ADD profile_image VARCHAR(255) DEFAULT 'default.png'"))
    
    # 2. Staff/HOD Profile
    results.append("Staff Profile: " + add_col("ALTER TABLE staff ADD profile_image VARCHAR(255) DEFAULT 'default.png'"))
    results.append("HOD Profile: " + add_col("ALTER TABLE hod ADD profile_image VARCHAR(255) DEFAULT 'default.png'"))

    # 3. Staff Timetable
    results.append("Staff Timetable: " + add_col("ALTER TABLE staff ADD timetable_file VARCHAR(255)"))
    
    # 4. OTP Columns (Ensure these exist for password reset)
    for table in ['admin', 'staff', 'hod']:
        results.append(f"{table} OTP Hash: " + add_col(f"ALTER TABLE {table} ADD otp_hash VARCHAR(255) DEFAULT NULL"))
        results.append(f"{table} OTP Expiry: " + add_col(f"ALTER TABLE {table} ADD otp_expiry DATETIME DEFAULT NULL"))

    try:
        db.session.commit()
    except:
        db.session.rollback()

    return f"<h1>DB Fix Results</h1><ul><li>{'</li><li>'.join(results)}</li></ul>"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)

with app.app_context():
    db.create_all()
    print("Tables check complete.")