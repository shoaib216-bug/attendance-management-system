from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class Admin(UserMixin, db.Model):
    id=db.Column(db.Integer, primary_key=True); username=db.Column(db.String(50), unique=True, nullable=False); password=db.Column(db.String(255), nullable=False)
    def get_id(self): return f'admin-{self.id}'
    def set_password(self, password): self.password = generate_password_hash(password)
    def check_password(self, password): return check_password_hash(self.password, password)

class Staff(UserMixin, db.Model):
    staff_id=db.Column(db.Integer, primary_key=True)
    name=db.Column(db.String(100), nullable=False)
    username=db.Column(db.String(50), unique=True, nullable=False)
    password=db.Column(db.String(255), nullable=False)
    branch=db.Column(db.String(50))
    # I REMOVED THE SUBJECT LINE HERE
    contact_no=db.Column(db.String(15))

    def get_id(self): return f'staff-{self.staff_id}'
    def set_password(self, password): self.password = generate_password_hash(password)
    def check_password(self, password): return check_password_hash(self.password, password)

class Student(db.Model):
    student_id=db.Column(db.Integer, primary_key=True); name=db.Column(db.String(100), nullable=False); roll_no=db.Column(db.String(20), unique=True, nullable=False); branch=db.Column(db.String(50)); semester=db.Column(db.Integer); parent_contact=db.Column(db.String(15), nullable=False)

class Attendance(db.Model):
    id=db.Column(db.Integer, primary_key=True); staff_id=db.Column(db.Integer, db.ForeignKey('staff.staff_id')); student_id=db.Column(db.Integer, db.ForeignKey('student.student_id')); date=db.Column(db.Date, nullable=False); period=db.Column(db.Integer, nullable=False);subject = db.Column(db.String(100), nullable=False); status=db.Column(db.Enum('Present', 'Absent'), nullable=False); timestamp=db.Column(db.DateTime, default=datetime.utcnow); student=db.relationship('Student', backref='attendances'); staff=db.relationship('Staff', backref='attendances')

# =========================================================================
# === THESE ARE THE MISSING MODELS THAT CAUSED THE CRASH ===
# =========================================================================
class Semester(db.Model):
    __tablename__='semesters'
    id = db.Column(db.Integer, primary_key=True)
    branch = db.Column(db.String(100), nullable=False)
    semester_num = db.Column(db.Integer, nullable=False)
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    is_active = db.Column(db.Boolean, default=True)

class Setting(db.Model):
    __tablename__='settings'
    id = db.Column(db.Integer, primary_key=True)
    setting_key = db.Column(db.String(50), unique=True, nullable=False)
    setting_value = db.Column(db.String(255))
# =========================================================================