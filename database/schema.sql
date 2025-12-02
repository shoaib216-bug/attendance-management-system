

-- 1. Create Database only if it doesn't exist
CREATE DATABASE IF NOT EXISTS attendance_management;
USE attendance_management;

-- 2. Create Admin Table
CREATE TABLE IF NOT EXISTS admin (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL
);

-- 3. Create Staff Table (Corrected: NO Subject Column)
CREATE TABLE IF NOT EXISTS staff (
    staff_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    branch VARCHAR(50),
    contact_no VARCHAR(15)
);

-- 4. Create Student Table
CREATE TABLE IF NOT EXISTS student (
    student_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    roll_no VARCHAR(20) UNIQUE NOT NULL,
    branch VARCHAR(50),
    semester INT,
    parent_contact VARCHAR(15) NOT NULL
);

-- 5. Create Semesters Table
CREATE TABLE IF NOT EXISTS semesters (
    id INT AUTO_INCREMENT PRIMARY KEY,
    branch VARCHAR(100) NOT NULL,
    semester_num INT NOT NULL,
    start_date DATE,
    end_date DATE,
    is_active BOOLEAN DEFAULT TRUE,
    UNIQUE KEY `unique_semester` (`branch`, `semester_num`)
);

-- 6. Create Settings Table
CREATE TABLE IF NOT EXISTS settings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    setting_key VARCHAR(50) UNIQUE NOT NULL,
    setting_value VARCHAR(255)
);

-- 7. Create Attendance Table
CREATE TABLE IF NOT EXISTS attendance (
    id INT AUTO_INCREMENT PRIMARY KEY,
    staff_id INT,
    student_id INT,
    date DATE NOT NULL,
    period INT NOT NULL,
    subject VARCHAR(100) NOT NULL,
    status ENUM('Present', 'Absent') NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (staff_id) REFERENCES staff(staff_id) ON DELETE SET NULL,
    FOREIGN KEY (student_id) REFERENCES student(student_id) ON DELETE CASCADE,
    UNIQUE KEY `unique_period_attendance` (`student_id`, `date`, `period`)
);

-- 8. Insert Default Settings (Only if they don't exist yet)
-- 'INSERT IGNORE' ensures this won't crash if settings are already there.
INSERT IGNORE INTO settings (setting_key, setting_value) VALUES
('college_latitude', '0.0'),
('college_longitude', '0.0'),
('allowed_radius_meters', '200'),
('geolocation_enabled', 'true');

SELECT 'Database structure verified. No data was deleted.' AS status;