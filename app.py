import os
from flask import Flask, redirect, url_for
from flask_login import LoginManager
from config import Config
from models.models import db, Admin, Staff # Only import users who can log in
from routes.auth_routes import auth_bp
from routes.admin_routes import admin_bp
from routes.staff_routes import staff_bp
from routes.public_routes import public_bp # Import the new public blueprint

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.admin_login'

@app.context_processor
def inject_user_types():
    # Only Admin and Staff are loginable user types now
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

# Register only the blueprints we are using
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(staff_bp, url_prefix='/staff')
app.register_blueprint(public_bp, url_prefix='/view') # The public view pages

@app.route('/')
def index():
    # The "Register First" logic is still useful for initial setup
    with app.app_context():
        if Admin.query.first() is None:
            return redirect(url_for('auth.register_admin'))
        else:
            return redirect(url_for('auth.admin_login'))

if __name__ == '__main__':
    app.run(debug=True)