import os
from flask import Blueprint, render_template, redirect, url_for, flash, request, session, current_app
from flask_login import login_user, logout_user, login_required, current_user
from models.models import db, Admin, Staff, HOD
import random
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from services.sms_service import send_otp_sms
from utils.validators import is_valid_username, is_valid_password

auth_bp = Blueprint('auth', __name__)

# =========================================================
# === 1. REGISTRATION ===
# =========================================================
@auth_bp.route('/register', methods=['GET', 'POST'])
def register_admin():
    MY_SECRET_KEY = "SHOAIB216"
    provided_key = request.args.get('key')
    admin_exists = Admin.query.first() is not None

    if admin_exists and provided_key != MY_SECRET_KEY:
        flash('Access Denied. Registration is restricted.', 'danger')
        return redirect(url_for('auth.admin_login'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        contact_no = request.form.get('contact_no')

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

        new_admin = Admin(username=username, email=email, contact_no=contact_no)
        new_admin.set_password(password)
        db.session.add(new_admin)
        db.session.commit()
        
        flash('New Admin account created successfully! Please log in.', 'success')
        return redirect(url_for('auth.admin_login'))

    return render_template('auth/register.html')

# =========================================================
# === 2. LOGIN ROUTES (Admin, Staff, HOD) ===
# =========================================================
@auth_bp.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        admin = Admin.query.filter_by(username=username).first()
        
        if admin and admin.check_password(password):
            login_user(admin, remember=True)
            return redirect(url_for('admin.dashboard'))
            
        flash('Invalid username or password.', 'danger')
    return render_template('auth/admin_login.html')

@auth_bp.route('/staff/login', methods=['GET', 'POST'])
def staff_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        staff = Staff.query.filter_by(username=username).first()
        
        if staff and staff.check_password(password):
            login_user(staff, remember=True)
            return redirect(url_for('staff.dashboard'))
            
        flash('Invalid username or password.', 'danger')
    return render_template('auth/staff_login.html')

@auth_bp.route('/hod/login', methods=['GET', 'POST'])
def hod_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        hod = HOD.query.filter_by(username=username).first()
        
        if hod and hod.check_password(password):
            login_user(hod, remember=True)
            return redirect(url_for('hod.dashboard'))
            
        flash('Invalid HOD username or password.', 'danger')
    return render_template('auth/hod_login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.admin_login'))

# =========================================================
# === 3. PROFILE MANAGEMENT (Upload/Edit/Username Change) ===
# =========================================================
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        action = request.form.get('action')

        # --- UPDATE INFO (Username, Name, Contact) ---
        if action == 'update_info':
            new_username = request.form.get('username')
            new_name = request.form.get('name')
            new_contact = request.form.get('contact_no')
            
            # Validate Username Uniqueness if changed
            if new_username and new_username != current_user.username:
                existing = None
                if isinstance(current_user, Admin): existing = Admin.query.filter_by(username=new_username).first()
                elif isinstance(current_user, Staff): existing = Staff.query.filter_by(username=new_username).first()
                elif isinstance(current_user, HOD): existing = HOD.query.filter_by(username=new_username).first()
                
                if existing:
                    flash('Username already taken.', 'danger')
                    return redirect(url_for('auth.profile'))
                current_user.username = new_username

            if new_name: current_user.name = new_name
            if new_contact: current_user.contact_no = new_contact
            
            if hasattr(current_user, 'email'):
                current_user.email = request.form.get('email')

            db.session.commit()
            flash('Profile updated successfully.', 'success')
            return redirect(url_for('auth.profile'))

        # --- UPLOAD PHOTO ---
        elif action == 'upload_photo':
            if 'profile_image' not in request.files:
                flash('No file part', 'danger'); return redirect(request.url)
            file = request.files['profile_image']
            if file.filename == '':
                flash('No selected file', 'danger'); return redirect(request.url)
            
            if file and allowed_file(file.filename):
                filename = secure_filename(f"{current_user.get_id()}_{file.filename}")
                if not os.path.exists(current_app.config['UPLOAD_FOLDER']):
                    os.makedirs(current_app.config['UPLOAD_FOLDER'])
                file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                current_user.profile_image = filename
                db.session.commit()
                flash('Photo updated!', 'success')
                return redirect(url_for('auth.profile'))
            else:
                flash('Invalid file type.', 'danger')

    return render_template('auth/profile.html', user=current_user)

@auth_bp.route('/profile/delete-photo', methods=['POST'])
@login_required
def delete_profile_photo():
    if current_user.profile_image != 'default.png':
        current_user.profile_image = 'default.png'
        db.session.commit()
        flash('Photo removed.', 'info')
    return redirect(url_for('auth.profile'))

# =========================================================
# === 4. CHANGE PASSWORD (OTP) ===
# =========================================================
@auth_bp.route('/profile/change-password-request', methods=['POST'])
@login_required
def change_password_request():
    if not current_user.contact_no:
        flash('Update contact number first.', 'warning')
        return redirect(url_for('auth.profile'))
    
    otp = str(random.randint(100000, 999999))
    try:
        current_user.otp_hash = generate_password_hash(otp)
        current_user.otp_expiry = datetime.utcnow() + timedelta(minutes=10)
        db.session.commit()
        send_otp_sms(current_user.contact_no, otp)
        flash(f'OTP sent to {current_user.contact_no}.', 'info')
        return redirect(url_for('auth.change_password_verify'))
    except Exception as e:
        flash(f'Error: {e}', 'danger')
        return redirect(url_for('auth.profile'))

@auth_bp.route('/profile/change-password-verify', methods=['GET', 'POST'])
@login_required
def change_password_verify():
    if request.method == 'POST':
        otp_input = request.form.get('otp')
        new_pass = request.form.get('new_password')
        confirm_pass = request.form.get('confirm_password')

        if new_pass != confirm_pass:
            flash('Passwords mismatch.', 'danger')
            return render_template('auth/verify_change_password.html')

        if current_user.otp_hash and current_user.otp_expiry > datetime.utcnow():
            if check_password_hash(current_user.otp_hash, otp_input):
                current_user.set_password(new_pass)
                current_user.otp_hash = None
                current_user.otp_expiry = None
                db.session.commit()
                flash('Password changed!', 'success')
                return redirect(url_for('auth.profile'))
            flash('Invalid OTP.', 'danger')
        else:
            flash('OTP Expired.', 'danger')
            return redirect(url_for('auth.profile'))

    return render_template('auth/verify_change_password.html')

# =========================================================
# === 5. FORGOT PASSWORD (Public) ===
# =========================================================
@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        user_type = request.form.get('user_type')
        identifier = request.form.get('identifier')
        user, phone_number = None, None

        if user_type == 'admin':
            user = Admin.query.filter_by(username=identifier).first()
            if user and hasattr(user, 'contact_no'): phone_number = user.contact_no
        elif user_type == 'staff':
            user = Staff.query.filter_by(username=identifier).first()
            if user: phone_number = user.contact_no
        elif user_type == 'hod':
            user = HOD.query.filter_by(username=identifier).first()
            if user: phone_number = user.contact_no
        
        if user and phone_number:
            otp = str(random.randint(100000, 999999))
            try:
                user.otp_hash = generate_password_hash(otp)
                user.otp_expiry = datetime.utcnow() + timedelta(minutes=10)
                db.session.commit()
                send_otp_sms(phone_number, otp)
                flash('OTP sent.', 'info')
                session['reset_user_type'] = user_type
                session['reset_user_identifier'] = identifier
                return redirect(url_for('auth.verify_otp'))
            except Exception as e:
                flash(f"Error: {e}", 'danger')
        else:
            flash('User not found or contact missing.', 'danger')
    return render_template('auth/forgot_password.html')

@auth_bp.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    if 'reset_user_identifier' not in session: return redirect(url_for('auth.forgot_password'))
    if request.method == 'POST':
        otp_from_user = request.form.get('otp')
        identifier = session.get('reset_user_identifier')
        user_type = session.get('reset_user_type')
        
        user = None
        if user_type == 'admin': user = Admin.query.filter_by(username=identifier).first()
        elif user_type == 'staff': user = Staff.query.filter_by(username=identifier).first()
        elif user_type == 'hod': user = HOD.query.filter_by(username=identifier).first()
            
        if user and hasattr(user, 'otp_hash') and user.otp_hash and user.otp_expiry > datetime.utcnow():
            if check_password_hash(user.otp_hash, otp_from_user):
                session['can_reset_password'] = True
                flash('OTP verified.', 'success')
                return redirect(url_for('auth.reset_password'))
        flash('Invalid/Expired OTP.', 'danger')
    return render_template('auth/verify_otp.html')

@auth_bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if 'can_reset_password' not in session: return redirect(url_for('auth.forgot_password'))
    if request.method == 'POST':
        new_pw = request.form.get('new_password')
        conf_pw = request.form.get('confirm_password')
        if new_pw != conf_pw:
            flash('Passwords mismatch.', 'danger')
            return render_template('auth/reset_password.html')
        
        identifier = session.get('reset_user_identifier')
        user_type = session.get('reset_user_type')
        user = None
        if user_type == 'admin': user = Admin.query.filter_by(username=identifier).first()
        elif user_type == 'staff': user = Staff.query.filter_by(username=identifier).first()
        elif user_type == 'hod': user = HOD.query.filter_by(username=identifier).first()
        
        if user:
            user.set_password(new_pw)
            user.otp_hash = None
            user.otp_expiry = None
            db.session.commit()
            session.clear()
            flash('Password reset. Login now.', 'success')
            return redirect(url_for(f'auth.{user_type}_login'))
    return render_template('auth/reset_password.html')