from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
# CORRECTED: Parent is removed. We only import what we need.
from models.models import db, Student, Staff, Admin, Semester, Setting, Attendance
from functools import wraps
from sqlalchemy import or_
from datetime import datetime

admin_bp = Blueprint('admin', __name__)

# --- This decorator is correct ---
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not isinstance(current_user, Admin):
            flash('This area is restricted to administrators.', 'danger')
            return redirect(url_for('auth.admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# --- Core Admin Routes ---

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    return render_template('admin/dashboard.html')

# =========================================================================
# === THIS IS THE CORRECTED, SIMPLIFIED add_student FUNCTION ===
# =========================================================================
@admin_bp.route('/add-student', methods=['GET', 'POST'])
@login_required
@admin_required
def add_student():
    if request.method == 'POST':
        roll_no = request.form.get('roll_no')
        parent_contact = request.form.get('parent_contact')

        # Check for duplicate roll number
        if Student.query.filter_by(roll_no=roll_no).first():
            flash(f'Roll Number {roll_no} is already registered.', 'danger')
            return render_template('admin/add_student.html', form_data=request.form)

        # Create a new student with the simple parent_contact field
        new_student = Student(
            name=request.form.get('name'), 
            roll_no=roll_no, 
            branch=request.form.get('branch'), 
            semester=request.form.get('semester'),
            parent_contact=parent_contact
        )
        db.session.add(new_student)
        db.session.commit()
        flash(f'Student "{new_student.name}" added successfully!', 'success')
        return redirect(url_for('admin.view_students'))
        
    return render_template('admin/add_student.html')
# =========================================================================

@admin_bp.route('/add-staff', methods=['GET', 'POST'])
@login_required
@admin_required
def add_staff():
    if request.method == 'POST':
        if Staff.query.filter_by(username=request.form.get('username')).first():
            flash('This staff username is already taken.', 'danger')
            return render_template('admin/add_staff.html', form_data=request.form)
        new_staff = Staff(
            name=request.form.get('name'), 
            username=request.form.get('username'), 
            branch=request.form.get('branch'), 
            subject=request.form.get('subject'), 
            contact_no=request.form.get('contact_no')
        )
        new_staff.set_password(request.form.get('password'))
        db.session.add(new_staff)
        db.session.commit()
        flash('Staff added successfully!', 'success')
        return redirect(url_for('admin.view_staff'))
    return render_template('admin/add_staff.html')

@admin_bp.route('/view-students')
@login_required
@admin_required
def view_students():
    search_query = request.args.get('q', '')
    if search_query:
        search_term = f"%{search_query}%"
        students = Student.query.filter(or_(Student.name.ilike(search_term), Student.roll_no.ilike(search_term))).order_by(Student.roll_no).all()
    else:
        students = Student.query.order_by(Student.roll_no).all()
    return render_template('admin/view_students.html', students=students, search_query=search_query)

@admin_bp.route('/view-staff')
@login_required
@admin_required
def view_staff():
    return render_template('admin/view_staff.html', staff=Staff.query.all())

# --- Feature Routes ---

@admin_bp.route('/manage-semesters', methods=['GET', 'POST'])
@login_required
@admin_required
def manage_semesters():
    if request.method == 'POST':
        branch, sem_num = request.form.get('branch'), request.form.get('semester_num')
        start_date, end_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d').date(), datetime.strptime(request.form.get('end_date'), '%Y-%m-%d').date()
        if Semester.query.filter_by(branch=branch, semester_num=sem_num).first():
            flash('This semester already exists.', 'warning')
        else:
            db.session.add(Semester(branch=branch, semester_num=sem_num, start_date=start_date, end_date=end_date))
            db.session.commit()
            flash('New semester created!', 'success')
        return redirect(url_for('admin.manage_semesters'))
    semesters = Semester.query.order_by(Semester.is_active.desc(), Semester.branch, Semester.semester_num).all()
    return render_template('admin/manage_semesters.html', semesters=semesters)

@admin_bp.route('/end-semester/<int:sem_id>', methods=['POST'])
@login_required
@admin_required
def end_semester(sem_id):
    sem = Semester.query.get_or_404(sem_id)
    sem.is_active = False
    students = Student.query.filter_by(branch=sem.branch, semester=sem.semester_num).all()
    count = 0
    for student in students:
        if student.semester < 8:
            student.semester += 1
            count += 1
    db.session.commit()
    flash(f'Semester {sem.semester_num} for {sem.branch} ended. {count} student(s) promoted.', 'success')
    return redirect(url_for('admin.manage_semesters'))

@admin_bp.route('/settings', methods=['GET', 'POST'])
@login_required
@admin_required
def settings():
    if request.method == 'POST':
        Setting.query.filter_by(setting_key='college_latitude').first().setting_value = request.form.get('latitude')
        Setting.query.filter_by(setting_key='college_longitude').first().setting_value = request.form.get('longitude')
        Setting.query.filter_by(setting_key='allowed_radius_meters').first().setting_value = request.form.get('radius')
        db.session.commit()
        flash('Settings updated successfully!', 'success')
        return redirect(url_for('admin.settings'))
    settings = {s.setting_key: s.setting_value for s in Setting.query.all()}
    return render_template('admin/settings.html', settings=settings)
# Add this code to the end of your /routes/admin_routes.py file

# =========================================================================
# === NEW ROUTE FOR VIEWING A SINGLE STUDENT'S DETAILS ===
# =========================================================================
@admin_bp.route('/student/<int:student_id>')
@login_required
@admin_required
def student_details(student_id):
    # Get the specific student from the database, or show a 404 error if not found
    student = Student.query.get_or_404(student_id)
    
    # Get all attendance records for this specific student
    records = Attendance.query.filter_by(student_id=student.student_id).order_by(Attendance.date.desc(), Attendance.period.desc()).all()
    
    # Calculate their attendance percentage
    total = len(records)
    present = len([r for r in records if r.status == 'Present'])
    percentage = (present / total * 100) if total > 0 else 0
    
    # Render the new details template with all the data
    return render_template(
        'admin/student_details.html', 
        student=student, 
        records=records, 
        percentage=percentage
    )
# =========================================================================