-- V8__create_stipends.sql
USE student_registration_db;

CREATE TABLE IF NOT EXISTS stipends (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    month VARCHAR(7) NOT NULL, -- e.g. '2025-01'
    amount DECIMAL(10,2) NOT NULL DEFAULT 0,
    status ENUM('submitted','approved','paid','rejected')
        DEFAULT 'submitted',

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_stipends_student
      FOREIGN KEY (student_id) REFERENCES students(id)
      ON DELETE CASCADE
);

CREATE UNIQUE INDEX idx_stipend_unique
    ON stipends(student_id, month);
