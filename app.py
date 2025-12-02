import os
from datetime import timedelta
from flask import Flask, redirect, url_for
from flask_login import LoginManager
from config import Config
from models.models import db, Admin, Staff 
from routes.auth_routes import auth_bp
from routes.admin_routes import admin_bp
from routes.staff_routes import staff_bp
from routes.public_routes import public_bp 

app = Flask(__name__)
app.config.from_object(Config)

# =========================================================
# === NEW: SESSION EXPIRATION CONFIGURATION ===
# This sets the session to expire after 15 days.
# Users will need to login roughly twice a month.
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

@app.context_processor
def inject_user_types():
    return dict(isinstance=isinstance, Admin=Admin, Staff=Staff)

@login_manager.user_loader
def load_user(user_id_string):
    """Loads only Admin and Staff users from the session."""
    try:
        user_type, user_id = user_id_string.split('-')
        user_id = int(user_id)
    except (ValueError, AttributeError): return None
    if user_type == 'admin': return Admin.query.get(user_id)
    elif user_type == 'staff': return Staff.query.get(user_id)
    return None

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(staff_bp, url_prefix='/staff')
app.register_blueprint(public_bp, url_prefix='/view') 

@app.route('/')
def index():
    with app.app_context():
        if Admin.query.first() is None:
            return redirect(url_for('auth.register_admin'))
        else:
            return redirect(url_for('auth.admin_login'))

if __name__ == '__main__':
    app.run(debug=True)