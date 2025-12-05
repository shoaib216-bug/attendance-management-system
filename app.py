import os
from datetime import timedelta
from flask import Flask, redirect, url_for
from flask_login import LoginManager
from config import Config

# 1. UPDATE: Imported HOD here
from models.models import db, Admin, Staff, HOD 

from routes.auth_routes import auth_bp
from routes.admin_routes import admin_bp
from routes.staff_routes import staff_bp
from routes.public_routes import public_bp

# 2. UPDATE: Imported the new HOD blueprint
from routes.hod_routes import hod_bp 

app = Flask(__name__)
app.config.from_object(Config)

# =========================================================
# === SESSION EXPIRATION CONFIGURATION ===
# =========================================================
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=15)

# =========================================================================
# === CACHE CONTROL HEADERS ===
# =========================================================================
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

# 3. UPDATE: Added HOD to context processor so templates can check 'isinstance(user, HOD)'
@app.context_processor
def inject_user_types():
    return dict(isinstance=isinstance, Admin=Admin, Staff=Staff, HOD=HOD)

# 4. UPDATE: Added logic to load HOD users
@login_manager.user_loader
def load_user(user_id_string):
    """Loads Admin, Staff, or HOD users from the session."""
    try:
        user_type, user_id = user_id_string.split('-')
        user_id = int(user_id)
    except (ValueError, AttributeError):
        return None

    if user_type == 'admin':
        return Admin.query.get(user_id)
    elif user_type == 'staff':
        return Staff.query.get(user_id)
    elif user_type == 'hod':  # <--- Added HOD check
        return HOD.query.get(user_id)
    return None

# 5. UPDATE: Registered the HOD blueprint
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(staff_bp, url_prefix='/staff')
app.register_blueprint(hod_bp, url_prefix='/hod') # <--- HOD Routes registered here
app.register_blueprint(public_bp, url_prefix='/view') 

@app.route('/')
def index():
    with app.app_context():
        # Checks if ANY admin exists. If not, go to register.
        if Admin.query.first() is None:
            return redirect(url_for('auth.register_admin'))
        else:
            return redirect(url_for('auth.admin_login'))

# ================================
# === Render Health Check Route ===
# ================================
@app.route('/healthz')
def health_check():
    return "OK", 200

# ================================
# === Render Production Server ===
# ================================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

# Database creation (Ensure this runs)
with app.app_context():
    db.create_all()
    print("Tables created successfully!")