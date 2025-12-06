from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

# --- 1. ADMIN MODEL (UPDATED) ---
class Admin(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    
    # NEW FIELDS
    email = db.Column(db.String(100), unique=True, nullable=True)
    contact_no = db.Column(db.String(15), nullable=True)
    profile_image = db.Column(db.String(255), nullable=False, default='default.png')

    def get_id(self): return f'admin-{self.id}'
    def set_password(self, password): self.password = generate_password_hash(password)
    def check_password(self, password): return check_password_hash(self.password, password)

# --- 2. STAFF MODEL ---
class Staff(UserMixin, db.Model):
    staff_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    branch = db.Column(db.String(50))
    contact_no = db.Column(db.String(15))
    timetable_file = db.Column(db.String(255), nullable=True)
    # NEW: Profile Image
    profile_image = db.Column(db.String(255), nullable=False, default='default.png')

    def get_id(self): return f'staff-{self.staff_id}'
    def set_password(self, password): self.password = generate_password_hash(password)
    def check_password(self, password): return check_password_hash(self.password, password)

# --- 3. HOD MODEL ---
class HOD(UserMixin, db.Model):
    __tablename__ = 'hod'
    hod_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    department = db.Column(db.String(50), nullable=False)
    contact_no = db.Column(db.String(15))
    # NEW: Profile Image
    profile_image = db.Column(db.String(255), nullable=False, default='default.png')

    def get_id(self): return f'hod-{self.hod_id}'
    def set_password(self, password): self.password = generate_password_hash(password)
    def check_password(self, password): return check_password_hash(self.password, password)

# --- 4. STUDENT MODEL ---
class Student(db.Model):
    student_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    roll_no = db.Column(db.String(20), unique=True, nullable=False)
    branch = db.Column(db.String(50))
    semester = db.Column(db.Integer)
    parent_contact = db.Column(db.String(15), nullable=False)

# --- 5. ATTENDANCE MODEL ---
class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    staff_id = db.Column(db.Integer, db.ForeignKey('staff.staff_id'))
    student_id = db.Column(db.Integer, db.ForeignKey('student.student_id'))
    date = db.Column(db.Date, nullable=False)
    period = db.Column(db.Integer, nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    status = db.Column(db.Enum('Present', 'Absent', name='attendance_status'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    student = db.relationship('Student', backref='attendances')
    staff = db.relationship('Staff', backref='attendances')

# --- 6. SEMESTER MODEL ---
class Semester(db.Model):
    __tablename__ = 'semesters'
    id = db.Column(db.Integer, primary_key=True)
    branch = db.Column(db.String(100), nullable=False)
    semester_num = db.Column(db.Integer, nullable=False)
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    is_active = db.Column(db.Boolean, default=True)

# --- 7. SETTINGS MODEL ---
class Setting(db.Model):
    __tablename__ = 'settings'
    id = db.Column(db.Integer, primary_key=True)
    setting_key = db.Column(db.String(50), unique=True, nullable=False)
    setting_value = db.Column(db.String(255))