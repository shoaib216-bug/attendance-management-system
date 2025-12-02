from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models.models import db, Student, Staff, Admin, Semester, Setting, Attendance
from functools import wraps
from sqlalchemy import or_
from datetime import datetime

admin_bp = Blueprint('admin', __name__)

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

@admin_bp.route('/add-student', methods=['GET', 'POST'])
@login_required
@admin_required
def add_student():
    if request.method == 'POST':
        roll_no = request.form.get('roll_no')
        if Student.query.filter_by(roll_no=roll_no).first():
            flash(f'Roll Number {roll_no} is already registered.', 'danger')
            return render_template('admin/add_student.html', form_data=request.form)

        new_student = Student(
            name=request.form.get('name'), 
            roll_no=roll_no, 
            branch=request.form.get('branch'), 
            semester=request.form.get('semester'),
            parent_contact=request.form.get('parent_contact')
        )
        db.session.add(new_student)
        db.session.commit()
        flash(f'Student "{new_student.name}" added successfully!', 'success')
        return redirect(url_for('admin.view_students'))
    return render_template('admin/add_student.html')

@admin_bp.route('/edit-student/<int:student_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_student(student_id):
    student = Student.query.get_or_404(student_id)
    if request.method == 'POST':
        student.name = request.form.get('name')
        student.branch = request.form.get('branch')
        student.semester = request.form.get('semester')
        student.parent_contact = request.form.get('parent_contact')
        
        db.session.commit()
        flash('Student details updated successfully!', 'success')
        return redirect(url_for('admin.view_students'))
    return render_template('admin/edit_student.html', student=student)

# =========================================================
# === NEW: DELETE SINGLE STUDENT ===
# =========================================================
@admin_bp.route('/delete-student/<int:student_id>', methods=['POST'])
@login_required
@admin_required
def delete_student(student_id):
    student = Student.query.get_or_404(student_id)
    
    # 1. Delete associated attendance records first
    Attendance.query.filter_by(student_id=student.student_id).delete()
    
    # 2. Delete the student
    db.session.delete(student)
    db.session.commit()
    
    flash(f'Student "{student.name}" and their attendance history have been deleted.', 'success')
    return redirect(url_for('admin.view_students'))

# =========================================================
# === NEW: DELETE ALL STUDENTS (RESET) ===
# =========================================================
@admin_bp.route('/delete-all-students', methods=['POST'])
@login_required
@admin_required
def delete_all_students():
    try:
        # 1. Delete ALL attendance records (needed because of foreign keys)
        num_attendance = db.session.query(Attendance).delete()
        
        # 2. Delete ALL students
        num_students = db.session.query(Student).delete()
        
        db.session.commit()
        flash(f'Database Reset: Deleted {num_students} students and {num_attendance} attendance records.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting students: {str(e)}', 'danger')
        
    return redirect(url_for('admin.view_students'))

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
            contact_no=request.form.get('contact_no')
        )
        new_staff.set_password(request.form.get('password'))
        db.session.add(new_staff)
        db.session.commit()
        flash('Staff added successfully!', 'success')
        return redirect(url_for('admin.view_staff'))
    return render_template('admin/add_staff.html')

@admin_bp.route('/edit-staff/<int:staff_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_staff(staff_id):
    staff = Staff.query.get_or_404(staff_id)
    if request.method == 'POST':
        staff.name = request.form.get('name')
        staff.username = request.form.get('username')
        staff.branch = request.form.get('branch')
        staff.contact_no = request.form.get('contact_no')
        
        new_password = request.form.get('password')
        if new_password:
            staff.set_password(new_password)
            
        db.session.commit()
        flash('Staff details updated successfully!', 'success')
        return redirect(url_for('admin.view_staff'))
    return render_template('admin/edit_staff.html', staff=staff)

@admin_bp.route('/delete-staff/<int:staff_id>', methods=['POST'])
@login_required
@admin_required
def delete_staff(staff_id):
    staff = Staff.query.get_or_404(staff_id)
    Attendance.query.filter_by(staff_id=staff.staff_id).delete()
    db.session.delete(staff)
    db.session.commit()
    flash(f'Staff member "{staff.name}" and their attendance logs have been deleted.', 'success')
    return redirect(url_for('admin.view_staff'))

@admin_bp.route('/view-students')
@login_required
@admin_required
def view_students():
    search_query = request.args.get('q', '').strip()
    selected_branch = request.args.get('branch', '')
    selected_semester = request.args.get('semester', '')

    query = Student.query

    if search_query:
        query = query.filter(or_(Student.name.ilike(f'%{search_query}%'), Student.roll_no.ilike(f'%{search_query}%')))
    if selected_branch:
        query = query.filter(Student.branch == selected_branch)
    if selected_semester:
        query = query.filter(Student.semester == int(selected_semester))

    students = query.order_by(Student.roll_no).all()
    
    all_students = Student.query.with_entities(Student.branch, Student.semester).all()
    available_branches = sorted(list(set([s.branch for s in all_students if s.branch])))
    available_semesters = sorted(list(set([s.semester for s in all_students if s.semester])))

    return render_template('admin/view_students.html', students=students, search_query=search_query, selected_branch=selected_branch, selected_semester=selected_semester, available_branches=available_branches, available_semesters=available_semesters)

@admin_bp.route('/view-staff')
@login_required
@admin_required
def view_staff():
    return render_template('admin/view_staff.html', staff=Staff.query.all())

@admin_bp.route('/student/<int:student_id>')
@login_required
@admin_required
def student_details(student_id):
    student = Student.query.get_or_404(student_id)
    records = db.session.query(Attendance).filter_by(student_id=student.student_id).order_by(Attendance.date.desc(), Attendance.period.desc()).all()
    total = len(records)
    present = len([r for r in records if r.status == 'Present'])
    percentage = (present / total * 100) if total > 0 else 0
    return render_template('admin/student_details.html', student=student, records=records, percentage=percentage)

# --- Other Routes ---
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
    flash(f'Semester {sem.semester_num} for {sem.branch} has been ended. {count} student(s) have been promoted.', 'success')
    return redirect(url_for('admin.manage_semesters'))

@admin_bp.route('/settings', methods=['GET', 'POST'])
@login_required
@admin_required
def settings():
    if request.method == 'POST':
        new_lat = request.form.get('latitude')
        new_lon = request.form.get('longitude')
        new_radius = request.form.get('radius')
        geolocation_enabled_val = request.form.get('geolocation_enabled')

        Setting.query.filter_by(setting_key='college_latitude').first().setting_value = new_lat
        Setting.query.filter_by(setting_key='college_longitude').first().setting_value = new_lon
        Setting.query.filter_by(setting_key='allowed_radius_meters').first().setting_value = new_radius
        Setting.query.filter_by(setting_key='geolocation_enabled').first().setting_value = geolocation_enabled_val
        
        db.session.commit()
        flash('Settings updated successfully!', 'success')
        return redirect(url_for('admin.settings'))

    settings_list = Setting.query.all()
    settings = {s.setting_key: s.setting_value for s in settings_list}
    return render_template('admin/settings.html', settings=settings)