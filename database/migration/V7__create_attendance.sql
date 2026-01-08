-- V7__create_attendance.sql
USE student_registration_db;

CREATE TABLE IF NOT EXISTS attendance (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    attendance_date DATE NOT NULL,
    status ENUM('present','absent','late','excused') DEFAULT 'present',

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_attendance_student
      FOREIGN KEY (student_id) REFERENCES students(id)
      ON DELETE CASCADE
);

CREATE UNIQUE INDEX idx_attendance_unique
    ON attendance(student_id, attendance_date);
