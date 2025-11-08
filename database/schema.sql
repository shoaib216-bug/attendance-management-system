-- Create the database if it doesn't exist
CREATE DATABASE IF NOT EXISTS college_management;

-- Use the created database
USE college_management;

-- Drop tables if they exist to ensure a clean slate
DROP TABLE IF EXISTS attendance;
DROP TABLE IF EXISTS student;
DROP TABLE IF EXISTS staff;
DROP TABLE IF EXISTS admin;

-- Create admin table
CREATE TABLE admin (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL
);

-- Insert a default admin user. Username: admin, Password: password
INSERT INTO admin (username, password) VALUES ('admin', 'pbkdf2:sha256:260000$hQGk3t5sJ3d9A2p1$d021c769411b339dcd292e3160b732731c34a6e3e57396a1a441b802e334f5a4');

-- Create staff table
CREATE TABLE staff (
    staff_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    branch VARCHAR(50),
    subject VARCHAR(100),
    contact_no VARCHAR(15)
);

-- Create student table
CREATE TABLE student (
    student_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    roll_no VARCHAR(20) UNIQUE NOT NULL,
    branch VARCHAR(50),
    semester INT,
    parent_contact VARCHAR(15) NOT NULL,
    password VARCHAR(255) NOT NULL
);

-- Create attendance table
CREATE TABLE attendance (
    id INT AUTO_INCREMENT PRIMARY KEY,
    staff_id INT,
    student_id INT,
    date DATE NOT NULL,
    status ENUM('Present', 'Absent') NOT NULL,
    FOREIGN KEY (staff_id) REFERENCES staff(staff_id) ON DELETE SET NULL,
    FOREIGN KEY (student_id) REFERENCES student(student_id) ON DELETE CASCADE,
    UNIQUE KEY unique_attendance (student_id, date)
);
