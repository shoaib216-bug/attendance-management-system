from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from models.models import db, Student, Attendance, Staff, Setting
from datetime import datetime
import pytz # <--- Import pytz for Timezone conversion
from sqlalchemy import distinct
from functools import wraps
from math import sin, cos, sqrt, atan2, radians
from services.sms_service import send_absent_notification_sms

staff_bp = Blueprint('staff', __name__)

# Helper function for IST Time
def get_ist_time():
    utc_now = datetime.utcnow()
    ist_tz = pytz.timezone('Asia/Kolkata')
    return utc_now.replace(tzinfo=pytz.utc).astimezone(ist_tz)

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
    # Use IST for checking today's attendance
    ist_now = get_ist_time()
    today = ist_now.date()
    
    if request.method == 'POST':
        branch, semester, period, subject = request.form.get('branch'), request.form.get('semester'), request.form.get('period'), request.form.get('subject')
        
        if not all([branch, semester, period, subject]):
            flash('All fields are required.', 'danger'); return redirect(url_for('staff.dashboard'))
        
        existing = Attendance.query.join(Student).filter(Student.branch == branch, Student.semester == semester, Attendance.date == today, Attendance.period == period).first()
        if existing:
            flash(f'Attendance for {branch} (Sem {semester}) for period {period} has already been taken by {existing.staff.name}.', 'warning'); return redirect(url_for('staff.dashboard'))
        
        students = Student.query.filter_by(branch=branch, semester=semester).order_by(Student.roll_no).all()
        if not students:
            flash('No students found for the selected criteria.', 'warning'); return redirect(url_for('staff.dashboard'))
        
        return render_template('staff/mark_attendance.html', students=students, date=today.strftime('%d-%m-%Y'), period=period, subject=subject)
    
    branches = [b[0] for b in db.session.query(distinct(Student.branch)).order_by(Student.branch).all()]
    semesters = [s[0] for s in db.session.query(distinct(Student.semester)).order_by(Student.semester).all()]
    return render_template('staff/dashboard.html', branches=branches, semesters=semesters)

@staff_bp.route('/submit-attendance', methods=['POST'])
@login_required
@staff_required
def submit_attendance():
    settings = {s.setting_key: s.setting_value for s in Setting.query.all()}
    if settings.get('geolocation_enabled') == 'true':
        user_lat, user_lon = request.form.get('latitude', type=float), request.form.get('longitude', type=float)
        if user_lat is None or user_lon is None:
            flash('Location data not provided. Please enable location services.', 'danger'); return redirect(url_for('staff.dashboard'))
        if not all(k in settings for k in ['college_latitude', 'college_longitude', 'allowed_radius_meters']):
            flash('Geolocation settings are not fully configured by the admin.', 'danger'); return redirect(url_for('staff.dashboard'))
        college_lat, college_lon = float(settings.get('college_latitude')), float(settings.get('college_longitude'))
        allowed_radius = int(settings.get('allowed_radius_meters'))
        distance = calculate_distance(college_lat, college_lon, user_lat, user_lon)
        if distance > allowed_radius:
            flash(f'Attendance submission failed. You are {int(distance)} meters away from campus.', 'danger'); return redirect(url_for('staff.dashboard'))
    
    student_ids, period, subject = request.form.getlist('student_id'), request.form.get('period'), request.form.get('subject')
    
    # GET EXACT IST TIME
    ist_now = get_ist_time()
    attendance_date = ist_now.date()
    time_str = ist_now.strftime('%I:%M %p') # e.g., "10:30 AM"

    if not all([period, subject]):
        flash('Error: Period or Subject information was missing.', 'danger'); return redirect(url_for('staff.dashboard'))

    for student_id in student_ids:
        status = request.form.get(f'status_{student_id}')
        if status:
            record = Attendance(staff_id=current_user.staff_id, student_id=student_id, date=attendance_date, period=int(period), subject=subject, status=status)
            db.session.add(record)
            if status == 'Absent':
                student = Student.query.get(student_id)
                if student and student.parent_contact:
                    # Pass the IST Time string to the SMS service
                    send_absent_notification_sms(
                        to_number=student.parent_contact, 
                        student_name=student.name, 
                        date_str=attendance_date.strftime('%d-%b-%Y'), 
                        period=period,
                        subject=subject,
                        time_str=time_str # <--- This is now IST time
                    )
    
    db.session.commit()
    success_message = f'Attendance for period {period} submitted successfully at {time_str}!'
    if settings.get('geolocation_enabled') == 'true':
        success_message = "Location Verified! " + success_message
    flash(success_message, 'success')
    return redirect(url_for('staff.dashboard'))

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
            except ValueError: flash('Invalid date format.', 'danger')
    return render_template('staff/attendance-history.html', records=records, search_date=search_date)