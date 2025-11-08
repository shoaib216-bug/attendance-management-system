from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required
from models.models import db, Admin, Staff
import random
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from services.sms_service import send_otp_sms

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register_admin():
    if Admin.query.first() is not None: return redirect(url_for('auth.admin_login'))
    if request.method == 'POST':
        username, password = request.form.get('username'), request.form.get('password')
        if not username or not password:
            flash('Username and password cannot be empty.', 'danger'); return render_template('auth/register.html')
        new_admin = Admin(username=username); new_admin.set_password(password)
        db.session.add(new_admin); db.session.commit()
        flash('Admin account created successfully! Please log in.', 'success'); return redirect(url_for('auth.admin_login'))
    return render_template('auth/register.html')

@auth_bp.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username, password = request.form.get('username'), request.form.get('password')
        admin = Admin.query.filter_by(username=username).first()
        if admin and admin.check_password(password):
            login_user(admin); return redirect(url_for('admin.dashboard'))
        flash('Invalid username or password.', 'danger')
    return render_template('auth/admin_login.html')

@auth_bp.route('/staff/login', methods=['GET', 'POST'])
def staff_login():
    if request.method == 'POST':
        username, password = request.form.get('username'), request.form.get('password')
        staff = Staff.query.filter_by(username=username).first()
        if staff and staff.check_password(password):
            login_user(staff); return redirect(url_for('staff.dashboard'))
        flash('Invalid username or password.', 'danger')
    return render_template('auth/staff_login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user(); flash('You have been logged out.', 'info'); return redirect(url_for('auth.admin_login'))

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        user_type, identifier = request.form.get('user_type'), request.form.get('identifier')
        user, phone_number = None, None
        if user_type == 'admin':
            user = Admin.query.filter_by(username=identifier).first()
            if not user or not hasattr(user, 'contact_no'): # Admin needs a contact_no field to get OTP
                flash('Admin password recovery via OTP is not configured.', 'warning'); return redirect(url_for('auth.forgot_password'))
            phone_number = user.contact_no
        elif user_type == 'staff':
            user = Staff.query.filter_by(username=identifier).first()
            if user: phone_number = user.contact_no
        
        if user and phone_number:
            otp = str(random.randint(100000, 999999))
            user.otp_hash, user.otp_expiry = generate_password_hash(otp), datetime.utcnow() + timedelta(minutes=10)
            db.session.commit(); send_otp_sms(phone_number, otp)
            flash('An OTP has been sent (check terminal).', 'info')
            session['reset_user_type'], session['reset_user_identifier'] = user_type, identifier
            return redirect(url_for('auth.verify_otp'))
        else:
            flash('User not found or no phone number is registered.', 'danger')
    return render_template('auth/forgot_password.html')

@auth_bp.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    if 'reset_user_identifier' not in session: return redirect(url_for('auth.forgot_password'))
    if request.method == 'POST':
        otp_from_user, identifier, user_type = request.form.get('otp'), session.get('reset_user_identifier'), session.get('reset_user_type')
        user = None
        if user_type == 'admin': user = Admin.query.filter_by(username=identifier).first()
        elif user_type == 'staff': user = Staff.query.filter_by(username=identifier).first()
        if user and user.otp_hash and user.otp_expiry > datetime.utcnow() and check_password_hash(user.otp_hash, otp_from_user):
            session['can_reset_password'] = True; flash('OTP verified. Please set a new password.', 'success'); return redirect(url_for('auth.reset_password'))
        flash('Invalid or expired OTP.', 'danger')
    return render_template('auth/verify_otp.html')

@auth_bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if 'can_reset_password' not in session: flash('Unauthorized access.', 'danger'); return redirect(url_for('auth.forgot_password'))
    if request.method == 'POST':
        new_password, confirm_password = request.form.get('new_password'), request.form.get('confirm_password')
        if not new_password or new_password != confirm_password:
            flash('Passwords do not match.', 'danger'); return render_template('auth/reset_password.html')
        identifier, user_type = session.get('reset_user_identifier'), session.get('reset_user_type')
        user = None
        if user_type == 'admin': user = Admin.query.filter_by(username=identifier).first()
        elif user_type == 'staff': user = Staff.query.filter_by(username=identifier).first()
        if user:
            user.set_password(new_password); user.otp_hash, user.otp_expiry = None, None
            db.session.commit(); session.clear()
            flash('Password reset successfully. Please log in.', 'success'); return redirect(url_for(f'auth.{user_type}_login'))
    return render_template('auth/reset_password.html')