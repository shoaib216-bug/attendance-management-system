from flask import Blueprint, render_template, request, flash
from models.models import Student, Attendance

public_bp = Blueprint('public', __name__)

@public_bp.route('/student', methods=['GET', 'POST'])
def view_student_attendance():
    student, records, percentage = None, [], 0
    if request.method == 'POST':
        roll_no = request.form.get('roll_no', '').strip()
        if not roll_no:
            flash('Please enter a Roll Number.', 'danger')
        else:
            student = Student.query.filter_by(roll_no=roll_no).first()
            if student:
                records = Attendance.query.filter_by(student_id=student.student_id).order_by(Attendance.date.desc(), Attendance.period.desc()).all()
                total = len(records)
                present = len([r for r in records if r.status == 'Present'])
                percentage = (present / total * 100) if total > 0 else 0
            else:
                flash(f'No student found with Roll Number "{roll_no}".', 'danger')
    return render_template('public/student_view.html', student=student, records=records, percentage=percentage)

@public_bp.route('/parent', methods=['GET', 'POST'])
def view_parent_attendance():
    student, records, percentage = None, [], 0
    if request.method == 'POST':
        phone_no = request.form.get('phone_no', '').strip()
        if not phone_no:
            flash('Please enter a Phone Number.', 'danger')
        else:
            # We search the student table directly for the parent's contact number
            student = Student.query.filter_by(parent_contact=phone_no).first()
            if student:
                records = Attendance.query.filter_by(student_id=student.student_id).order_by(Attendance.date.desc(), Attendance.period.desc()).all()
                total = len(records)
                present = len([r for r in records if r.status == 'Present'])
                percentage = (present / total * 100) if total > 0 else 0
            else:
                flash(f'No student record found for the Parent Phone Number "{phone_no}".', 'danger')
    return render_template('public/parent_view.html', student=student, records=records, percentage=percentage)