import os
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from sqlalchemy import func
from models.models import db, HOD, Staff, Student, Attendance
from functools import wraps

hod_bp = Blueprint('hod', __name__)

# --- SECURITY DECORATOR ---
def hod_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not isinstance(current_user, HOD):
            flash('Access restricted to HODs only.', 'danger')
            return redirect(url_for('auth.hod_login'))
        return f(*args, **kwargs)
    return decorated_function

# --- 1. DASHBOARD (Updated for General HOD) ---
@hod_bp.route('/dashboard')
@login_required
@hod_required
def dashboard():
    dept = current_user.department
    
    # --- GENERAL HOD LOGIC ---
    if dept == 'General':
        # See only 'General' Staff
        staff_count = Staff.query.filter_by(branch='General').count()
        
        # See ALL Students but ONLY Sem <= 4
        students = Student.query.filter(Student.semester <= 4).order_by(Student.roll_no).all()
    else:
        # Normal HOD Logic
        staff_count = Staff.query.filter_by(branch=dept).count()
        students = Student.query.filter_by(branch=dept).order_by(Student.roll_no).all()

    student_count = len(students)

    # Graph Data (Based on the 'students' list fetched above)
    sem_counts = [0] * 8 
    for s in students:
        try:
            sem = int(s.semester) 
            if 1 <= sem <= 8:
                sem_counts[sem - 1] += 1
        except: continue

    sem_labels = [f"Sem {i}" for i in range(1, 9)]
    
    return render_template('hod/dashboard.html', 
                           dept=dept, 
                           student_count=student_count, 
                           staff_count=staff_count,
                           students=students,      
                           sem_labels=sem_labels,  
                           sem_data=sem_counts)

# --- 2. STUDENT DETAILS (Updated Security) ---
@hod_bp.route('/student_details/<int:student_id>')
@login_required
@hod_required
def student_details(student_id):
    student = Student.query.get_or_404(student_id)
    hod_dept = current_user.department

    # --- AUTHORIZATION CHECK ---
    authorized = False
    if hod_dept == 'General':
        # General HOD can see any student as long as they are in Sem 1, 2, 3, or 4
        if student.semester and student.semester <= 4:
            authorized = True
        else:
            flash("Access Denied: General HOD can only view students in Semesters 1-4.", "danger")
    else:
        # Normal HOD check
        if hod_dept == student.branch:
            authorized = True
        else:
            flash(f"Access Denied: You represent {hod_dept}, but student is in {student.branch}.", "danger")

    if not authorized:
        return redirect(url_for('hod.dashboard'))

    # Fetch Attendance
    try:
        attendance_records = Attendance.query.filter_by(student_id=student.student_id).order_by(Attendance.date.desc()).all()
        total_classes = len(attendance_records)
        present_count = sum(1 for a in attendance_records if a.status == 'Present')
        percentage = (present_count / total_classes * 100) if total_classes > 0 else 0
    except:
        attendance_records = []
        total_classes = 0
        present_count = 0
        percentage = 0

    return render_template('hod/student_details.html', 
                           student=student,
                           attendance=attendance_records,
                           total=total_classes,
                           present=present_count,
                           percentage=round(percentage, 2))

# --- 3. VIEW STAFF LIST ---
@hod_bp.route('/my-staff')
@login_required
@hod_required
def view_dept_staff():
    # General HOD -> General Staff
    # CSE HOD -> CSE Staff
    staff_list = Staff.query.filter_by(branch=current_user.department).all()
    return render_template('hod/view_staff.html', staff=staff_list)

# --- 4. VIEW STUDENTS LIST ---
@hod_bp.route('/my-students')
@login_required
@hod_required
def view_dept_students():
    if current_user.department == 'General':
        students = Student.query.filter(Student.semester <= 4).order_by(Student.roll_no).all()
    else:
        students = Student.query.filter_by(branch=current_user.department).order_by(Student.roll_no).all()
    return render_template('hod/view_students.html', students=students)

# --- 5. STAFF DETAILS ---
@hod_bp.route('/staff_details/<int:staff_id>')
@login_required
@hod_required
def staff_details(staff_id):
    staff = Staff.query.get_or_404(staff_id)
    
    # Security Check
    if staff.branch != current_user.department:
        flash("Access Denied: This staff member is not in your department.", "danger")
        return redirect(url_for('hod.view_dept_staff'))

    attendance_history = db.session.query(
        Attendance.date, 
        Attendance.period, 
        Attendance.subject, 
        func.count(Attendance.id).label('student_count')
    ).filter_by(staff_id=staff.staff_id)\
     .group_by(Attendance.date, Attendance.period, Attendance.subject)\
     .order_by(Attendance.date.desc()).all()

    return render_template('hod/staff_details.html', staff=staff, history=attendance_history)

# --- 6. UPLOAD TIMETABLE ---
@hod_bp.route('/upload_timetable/<int:staff_id>', methods=['POST'])
@login_required
@hod_required
def upload_timetable(staff_id):
    staff = Staff.query.get_or_404(staff_id)
    
    if 'timetable' not in request.files:
        flash('No file part', 'danger')
        return redirect(url_for('hod.staff_details', staff_id=staff_id))
    
    file = request.files['timetable']
    
    if file.filename == '':
        flash('No selected file', 'danger')
        return redirect(url_for('hod.staff_details', staff_id=staff_id))

    if file:
        ext = file.filename.rsplit('.', 1)[1].lower()
        if ext not in ['png', 'jpg', 'jpeg', 'pdf', 'doc', 'docx', 'xls', 'xlsx']:
            flash('Invalid file type. Allowed: Images, PDF, Word, Excel', 'danger')
            return redirect(url_for('hod.staff_details', staff_id=staff_id))

        if staff.timetable_file:
            old_path = os.path.join(current_app.root_path, 'static', 'uploads', 'timetables', staff.timetable_file)
            if os.path.exists(old_path): os.remove(old_path)

        filename = secure_filename(f"staff_{staff.staff_id}_timetable.{ext}")
        upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'timetables')
        os.makedirs(upload_folder, exist_ok=True)
        file.save(os.path.join(upload_folder, filename))
        
        staff.timetable_file = filename
        db.session.commit()
        flash('Timetable uploaded successfully!', 'success')
        
    return redirect(url_for('hod.staff_details', staff_id=staff_id))

# --- 7. DELETE TIMETABLE ---
@hod_bp.route('/delete_timetable/<int:staff_id>', methods=['POST'])
@login_required
@hod_required
def delete_timetable(staff_id):
    staff = Staff.query.get_or_404(staff_id)
    if staff.timetable_file:
        file_path = os.path.join(current_app.root_path, 'static', 'uploads', 'timetables', staff.timetable_file)
        if os.path.exists(file_path): os.remove(file_path)
        staff.timetable_file = None
        db.session.commit()
        flash('Timetable deleted successfully.', 'success')
    else:
        flash('No timetable found.', 'warning')
    return redirect(url_for('hod.staff_details', staff_id=staff_id))