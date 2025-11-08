from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
# CORRECT: We import the models your code is actually using
from models.models import db, Student, Attendance, Staff, Setting
from datetime import datetime
from sqlalchemy import distinct
from functools import wraps
from math import sin, cos, sqrt, atan2, radians
# Make sure your sms_service.py has this function
from services.sms_service import send_absent_notification_sms

staff_bp = Blueprint('staff', __name__)

def staff_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not isinstance(current_user, Staff):
            flash('This area is restricted to staff members.', 'danger')
            return redirect(url_for('auth.staff_login'))
        return f(*args, **kwargs)
    return decorated_function

def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371e3; lat1_rad, lat2_rad = radians(lat1), radians(lat2); delta_lat, delta_lon = radians(lat2 - lat1), radians(lon2 - lon1)
    a = sin(delta_lat / 2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a)); return R * c

@staff_bp.route('/dashboard', methods=['GET', 'POST'])
@login_required
@staff_required
def dashboard():
    if request.method == 'POST':
        branch, semester, period = request.form.get('branch'), request.form.get('semester'), request.form.get('period')
        today = datetime.utcnow().date()
        existing = Attendance.query.join(Student).filter(Student.branch == branch, Student.semester == semester, Attendance.date == today, Attendance.period == period).first()
        if existing:
            flash(f'Attendance for {branch} (Sem {semester}) for period {period} has already been taken by {existing.staff.name}.', 'warning')
            return redirect(url_for('staff.dashboard'))
        students = Student.query.filter_by(branch=branch, semester=semester).order_by(Student.roll_no).all()
        if not students:
            flash('No students found for the selected criteria.', 'warning')
            return redirect(url_for('staff.dashboard'))
        return render_template('staff/mark_attendance.html', students=students, date=today.strftime('%d-%m-%Y'), period=period)
    
    branches = [b[0] for b in db.session.query(distinct(Student.branch)).order_by(Student.branch).all()]
    semesters = [s[0] for s in db.session.query(distinct(Student.semester)).order_by(Student.semester).all()]
    return render_template('staff/dashboard.html', branches=branches, semesters=semesters)

@staff_bp.route('/submit-attendance', methods=['POST'])
@login_required
@staff_required
def submit_attendance():
    user_lat = request.form.get('latitude', type=float)
    user_lon = request.form.get('longitude', type=float)
    if user_lat is None or user_lon is None:
        flash('Location data was not provided. Please enable location services.', 'danger')
        return redirect(url_for('staff.dashboard'))

    settings_list = Setting.query.all()
    if not settings_list or len(settings_list) < 3:
        flash('Geolocation settings are not fully configured by the admin yet.', 'danger')
        return redirect(url_for('staff.dashboard'))
        
    settings = {s.setting_key: s.setting_value for s in settings_list}
    college_lat, college_lon = float(settings.get('college_latitude', 0.0)), float(settings.get('college_longitude', 0.0))
    allowed_radius = int(settings.get('allowed_radius_meters', 200))
    distance = calculate_distance(college_lat, college_lon, user_lat, user_lon)
    if distance > allowed_radius:
        flash(f'Attendance submission failed. You are {int(distance)} meters away from campus, outside the allowed {allowed_radius}m radius.', 'danger')
        return redirect(url_for('staff.dashboard'))
    
    student_ids, period = request.form.getlist('student_id'), request.form.get('period')
    attendance_date = datetime.utcnow().date()
    if not period:
        flash('Error: Period information was missing. Please try again.', 'danger')
        return redirect(url_for('staff.dashboard'))

    for student_id in student_ids:
        status = request.form.get(f'status_{student_id}')
        if status:
            record = Attendance(staff_id=current_user.staff_id, student_id=student_id, date=attendance_date, period=int(period), status=status)
            db.session.add(record)
            
            if status == 'Absent':
                student = Student.query.get(student_id)
                if student and student.parent_contact:
                    send_absent_notification_sms(
                        to_number=student.parent_contact, 
                        student_name=student.name, 
                        date_str=attendance_date.strftime('%d-%m-%Y'), 
                        period=period
                    )

    db.session.commit()
    flash(f'Location Verified! Attendance for period {period} submitted successfully.', 'success')
    return redirect(url_for('staff.dashboard'))


# =========================================================================
# === THIS IS THE ONE AND ONLY 'attendance_history' FUNCTION ===
# The duplicate has been removed.
# =========================================================================
@staff_bp.route('/attendance-history', methods=['GET', 'POST'])
@login_required
@staff_required
def attendance_history():
    records, search_date = None, ""
    if request.method == 'POST':
        search_date = request.form.get('date')
        if search_date:
            try:
                date_obj = datetime.strptime(search_date, '%Y-%m-%d').date()
                records = Attendance.query.filter(Attendance.date == date_obj).join(Student).order_by(Attendance.period, Student.roll_no).all()
            except ValueError:
                flash('Invalid date format. Please use YYYY-MM-DD.', 'danger')
    
    return render_template('staff/attendance-history.html', records=records, search_date=search_date)