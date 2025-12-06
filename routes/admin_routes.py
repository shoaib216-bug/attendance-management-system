from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models.models import db, Student, Staff, Admin, HOD, Semester, Setting, Attendance
from functools import wraps
from sqlalchemy import or_, func
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

@admin_bp.route('/delete-student/<int:student_id>', methods=['POST'])
@login_required
@admin_required
def delete_student(student_id):
    student = Student.query.get_or_404(student_id)
    Attendance.query.filter_by(student_id=student.student_id).delete()
    db.session.delete(student)
    db.session.commit()
    flash(f'Student "{student.name}" and their attendance history have been deleted.', 'success')
    return redirect(url_for('admin.view_students'))

@admin_bp.route('/delete-all-students', methods=['POST'])
@login_required
@admin_required
def delete_all_students():
    try:
        num_attendance = db.session.query(Attendance).delete()
        num_students = db.session.query(Student).delete()
        db.session.commit()
        flash(f'Database Reset: Deleted {num_students} students and {num_attendance} attendance records.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting students: {str(e)}', 'danger')
    return redirect(url_for('admin.view_students'))

# --- STAFF MANAGEMENT ---
@admin_bp.route('/add-staff', methods=['GET', 'POST'])
@login_required
@admin_required
def add_staff():
    # 1. Fetch Branches and Add 'General'
    branches_data = db.session.query(Semester.branch).distinct().all()
    branches = [b[0] for b in branches_data]
    if "General" not in branches:
        branches.append("General")

    if request.method == 'POST':
        if Staff.query.filter_by(username=request.form.get('username')).first():
            flash('This staff username is already taken.', 'danger')
            return render_template('admin/add_staff.html', form_data=request.form, branches=branches)
        
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
    
    return render_template('admin/add_staff.html', branches=branches)

@admin_bp.route('/edit-staff/<int:staff_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_staff(staff_id):
    staff = Staff.query.get_or_404(staff_id)
    
    # 1. Fetch Branches and Add 'General'
    branches_data = db.session.query(Semester.branch).distinct().all()
    branches = [b[0] for b in branches_data]
    if "General" not in branches:
        branches.append("General")

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
    return render_template('admin/edit_staff.html', staff=staff, branches=branches)

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

# =========================================================
# === HOD MANAGEMENT ROUTES ===
# =========================================================

@admin_bp.route('/add-hod', methods=['GET', 'POST'])
@login_required
@admin_required
def add_hod():
    # 1. Fetch Branches and Add 'General' option
    branches_data = db.session.query(Semester.branch).distinct().all()
    branches = [b[0] for b in branches_data]
    if "General" not in branches:
        branches.append("General")

    if request.method == 'POST':
        username = request.form.get('username')
        if HOD.query.filter_by(username=username).first():
            flash('This HOD username is already taken.', 'danger')
            return render_template('admin/add_hod.html', branches=branches)

        new_hod = HOD(
            name=request.form.get('name'),
            username=username,
            department=request.form.get('department'),
            contact_no=request.form.get('contact_no')
        )
        new_hod.set_password(request.form.get('password'))
        db.session.add(new_hod)
        db.session.commit()
        flash(f'HOD for {new_hod.department} added successfully!', 'success')
        return redirect(url_for('admin.view_hods'))
    
    return render_template('admin/add_hod.html', branches=branches)

@admin_bp.route('/edit-hod/<int:hod_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_hod(hod_id):
    hod = HOD.query.get_or_404(hod_id)
    
    # 1. Fetch Branches and Add 'General'
    branches_data = db.session.query(Semester.branch).distinct().all()
    branches = [b[0] for b in branches_data]
    if "General" not in branches:
        branches.append("General")

    if request.method == 'POST':
        new_username = request.form.get('username')
        existing_hod = HOD.query.filter_by(username=new_username).first()
        if existing_hod and existing_hod.hod_id != hod.hod_id:
            flash('This username is already taken by another HOD.', 'danger')
        else:
            hod.name = request.form.get('name')
            hod.department = request.form.get('department')
            hod.contact_no = request.form.get('contact_no')
            hod.username = new_username
            new_password = request.form.get('password')
            if new_password and new_password.strip():
                hod.set_password(new_password)
            
            db.session.commit()
            flash('HOD details updated successfully!', 'success')
            return redirect(url_for('admin.view_hods'))

    return render_template('admin/edit_hod.html', hod=hod, branches=branches)


@admin_bp.route('/view-hods')
@login_required
@admin_required
def view_hods():
    hods = HOD.query.all()
    return render_template('admin/view_hods.html', hods=hods)

@admin_bp.route('/delete-hod/<int:hod_id>', methods=['POST'])
@login_required
@admin_required
def delete_hod(hod_id):
    hod = HOD.query.get_or_404(hod_id)
    db.session.delete(hod)
    db.session.commit()
    flash('HOD account deleted.', 'success')
    return redirect(url_for('admin.view_hods'))

# --- HOD Details for Admin View ---
@admin_bp.route('/hod/<int:hod_id>')
@login_required
@admin_required
def hod_details(hod_id):
    hod = HOD.query.get_or_404(hod_id)
    
    if hod.department == 'General':
        # General HOD Stats
        staff_count = Staff.query.filter_by(branch='General').count()
        students = Student.query.filter(Student.semester <= 4).order_by(Student.roll_no).all()
        student_count = len(students)
        
        # Graph Logic for Sem 1-4
        semester_stats = db.session.query(Student.semester, func.count(Student.student_id))\
            .filter(Student.semester <= 4)\
            .group_by(Student.semester)\
            .order_by(Student.semester).all()
    else:
        # Normal HOD Stats
        staff_count = Staff.query.filter_by(branch=hod.department).count()
        students = Student.query.filter_by(branch=hod.department).order_by(Student.roll_no).all()
        student_count = len(students)
        
        semester_stats = db.session.query(Student.semester, func.count(Student.student_id))\
            .filter_by(branch=hod.department)\
            .group_by(Student.semester)\
            .order_by(Student.semester).all()
    
    sem_labels = [f"Sem {s[0]}" for s in semester_stats]
    sem_data = [s[1] for s in semester_stats]

    return render_template('admin/hod_details.html', 
                           hod=hod, 
                           staff_count=staff_count, 
                           student_count=student_count,
                           sem_labels=sem_labels, 
                           sem_data=sem_data,
                           students=students)

# --- VIEW STUDENTS ---
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
        if selected_semester == 'Alumni':
            query = query.filter(Student.semester == None)
        else:
            query = query.filter(Student.semester == int(selected_semester))
    else:
        query = query.filter(Student.semester != None)

    students = query.order_by(Student.roll_no).all()
    
    all_students = Student.query.with_entities(Student.branch).all()
    available_branches = sorted(list(set([s.branch for s in all_students if s.branch])))
    available_semesters = [1, 2, 3, 4, 5, 6]
    
    return render_template('admin/view_students.html', 
                           students=students, 
                           search_query=search_query, 
                           selected_branch=selected_branch, 
                           selected_semester=selected_semester, 
                           available_branches=available_branches, 
                           available_semesters=available_semesters)

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
    promoted_count = 0
    graduated_count = 0
    for student in students:
        try:
            if student.semester is None: continue
            current_sem = int(student.semester)
            if current_sem < 6:
                student.semester = current_sem + 1
                promoted_count += 1
            elif current_sem == 6:
                student.semester = None
                graduated_count += 1
        except: continue
    db.session.commit()
    msg = f'Semester ended. {promoted_count} promoted.'
    if graduated_count > 0: msg += f' {graduated_count} graduates archived.'
    flash(msg, 'success')
    return redirect(url_for('admin.manage_semesters'))

@admin_bp.route('/settings', methods=['GET', 'POST'])
@login_required
@admin_required
def settings():
    if request.method == 'POST':
        # 1. Gather all possible settings from the form
        settings_map = {
            'college_latitude': request.form.get('latitude'),
            'college_longitude': request.form.get('longitude'),
            'allowed_radius_meters': request.form.get('radius'),
            'geolocation_enabled': request.form.get('geolocation_enabled')
        }

        # 2. Loop through each setting and Update OR Create (Upsert)
        for key, value in settings_map.items():
            if value is not None: # Check so we don't accidentally nullify things improperly
                setting_obj = Setting.query.filter_by(setting_key=key).first()
                
                if setting_obj:
                    # If setting exists, update it
                    setting_obj.setting_value = value
                else:
                    # If setting does NOT exist (Render empty DB), create it
                    new_setting = Setting(setting_key=key, setting_value=value)
                    db.session.add(new_setting)

        db.session.commit()
        flash('Settings updated successfully!', 'success')
        return redirect(url_for('admin.settings'))
    
    # GET Request: Display Settings
    settings_list = Setting.query.all()
    settings = {s.setting_key: s.setting_value for s in settings_list}
    return render_template('admin/settings.html', settings=settings)