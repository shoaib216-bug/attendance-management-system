from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from models.models import db, Admin, Staff
import random
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from services.sms_service import send_otp_sms
from utils.validators import is_valid_username, is_valid_password

auth_bp = Blueprint('auth', __name__)

# =========================================================
# === SECURE REGISTRATION ROUTE ===
# =========================================================
@auth_bp.route('/register', methods=['GET', 'POST'])
def register_admin():
    # 1. YOUR SECRET KEY
    MY_SECRET_KEY = "SHOAIB216"

    # 2. GET THE KEY FROM THE BROWSER URL (e.g. ?key=SHOAIB216)
    provided_key = request.args.get('key')

    # 3. CHECK IF SYSTEM IS ALREADY SET UP
    admin_exists = Admin.query.first() is not None

    # 4. STRICT SECURITY CHECK
    # If admins exist AND the key provided is WRONG or MISSING...
    # Then we BLOCK access and send them to the login page.
    if admin_exists and provided_key != MY_SECRET_KEY:
        flash('Access Denied. Registration is restricted.', 'danger')
        return redirect(url_for('auth.admin_login'))
    
    # --- Normal Registration Logic ---
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        is_username_ok, username_message = is_valid_username(username)
        if not is_username_ok:
            flash(username_message, 'danger')
            return render_template('auth/register.html')

        is_password_ok, password_message = is_valid_password(password)
        if not is_password_ok:
            flash(password_message, 'danger')
            return render_template('auth/register.html')

        if Admin.query.filter_by(username=username).first():
            flash('This username is already taken.', 'danger')
            return render_template('auth/register.html')

        new_admin = Admin(username=username)
        new_admin.set_password(password)
        db.session.add(new_admin)
        db.session.commit()
        
        flash('New Admin account created successfully! Please log in.', 'success')
        return redirect(url_for('auth.admin_login'))

    return render_template('auth/register.html')

# --- Admin Login ---
@auth_bp.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if current_user.is_authenticated:
        if isinstance(current_user, Admin):
            return redirect(url_for('admin.dashboard'))
        logout_user()
        flash('Logged out of previous session.', 'info')

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        admin = Admin.query.filter_by(username=username).first()
        
        if admin and admin.check_password(password):
            # Set session to be permanent and expire in 15 days
            session.permanent = True
            login_user(admin, remember=True, duration=timedelta(days=15))
            return redirect(url_for('admin.dashboard'))
            
        flash('Invalid username or password.', 'danger')
        
    return render_template('auth/admin_login.html')

# --- Staff Login ---
@auth_bp.route('/staff/login', methods=['GET', 'POST'])
def staff_login():
    if current_user.is_authenticated:
        if isinstance(current_user, Staff):
            return redirect(url_for('staff.dashboard'))
        logout_user()
        flash('Logged out of previous session.', 'info')

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        staff = Staff.query.filter_by(username=username).first()
        
        if staff and staff.check_password(password):
            # Set session to be permanent and expire in 15 days
            session.permanent = True
            login_user(staff, remember=True, duration=timedelta(days=15))
            return redirect(url_for('staff.dashboard'))
            
        flash('Invalid username or password.', 'danger')
        
    return render_template('auth/staff_login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    session.permanent = False # Clear permanent status
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.admin_login'))

# --- Forgot Password (ADMIN & STAFF ONLY) ---
@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        user_type = request.form.get('user_type')
        identifier = request.form.get('identifier')
        user = None
        phone_number = None

        # Handle Admin Logic
        if user_type == 'admin':
            user = Admin.query.filter_by(username=identifier).first()
            if user and hasattr(user, 'contact_no'):
                phone_number = user.contact_no
            else:
                flash('Admin OTP is not configured (No contact number found).', 'warning')
                return redirect(url_for('auth.forgot_password'))

        # Handle Staff Logic
        elif user_type == 'staff':
            user = Staff.query.filter_by(username=identifier).first()
            if user:
                phone_number = user.contact_no
        
        # If User Found & Phone Exists -> Send OTP
        if user and phone_number:
            otp = str(random.randint(100000, 999999))
            user.otp_hash = generate_password_hash(otp)
            user.otp_expiry = datetime.utcnow() + timedelta(minutes=10)
            db.session.commit()
            
            send_otp_sms(phone_number, otp)
            
            flash('An OTP has been sent to your registered mobile number.', 'info')
            session['reset_user_type'] = user_type
            session['reset_user_identifier'] = identifier
            return redirect(url_for('auth.verify_otp'))
        else:
            flash('User not found.', 'danger')

    return render_template('auth/forgot_password.html')

# --- OTP Verification ---
@auth_bp.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    if 'reset_user_identifier' not in session:
        return redirect(url_for('auth.forgot_password'))
        
    if request.method == 'POST':
        otp_from_user = request.form.get('otp')
        identifier = session.get('reset_user_identifier')
        user_type = session.get('reset_user_type')
        
        user = None
        if user_type == 'admin':
            user = Admin.query.filter_by(username=identifier).first()
        elif user_type == 'staff':
            user = Staff.query.filter_by(username=identifier).first()
            
        if user and user.otp_hash and user.otp_expiry > datetime.utcnow():
            if check_password_hash(user.otp_hash, otp_from_user):
                session['can_reset_password'] = True
                flash('OTP verified. Please set a new password.', 'success')
                return redirect(url_for('auth.reset_password'))
        
        flash('Invalid or expired OTP.', 'danger')
        
    return render_template('auth/verify_otp.html')

# --- Reset Password ---
@auth_bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if 'can_reset_password' not in session:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('auth.forgot_password'))
        
    if request.method == 'POST':
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if not new_password or new_password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('auth/reset_password.html')
            
        identifier = session.get('reset_user_identifier')
        user_type = session.get('reset_user_type')
        
        user = None
        if user_type == 'admin':
            user = Admin.query.filter_by(username=identifier).first()
        elif user_type == 'staff':
            user = Staff.query.filter_by(username=identifier).first()
            
        if user:
            user.set_password(new_password)
            user.otp_hash = None
            user.otp_expiry = None
            db.session.commit()
            session.clear()
            flash('Password reset successfully. Please log in.', 'success')
            return redirect(url_for(f'auth.{user_type}_login'))
            
    return render_template('auth/reset_password.html')