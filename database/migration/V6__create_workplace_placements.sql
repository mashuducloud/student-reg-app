-- V6__create_workplace_placements.sql
USE student_registration_db;

CREATE TABLE IF NOT EXISTS workplace_placements (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,

    employer_name    VARCHAR(255) NOT NULL,
    employer_contact VARCHAR(255),
    supervisor_name  VARCHAR(255),
    supervisor_phone VARCHAR(20),

    start_date DATE,
    end_date   DATE,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_placements_student
      FOREIGN KEY (student_id) REFERENCES students(id)
      ON DELETE CASCADE
);

CREATE INDEX idx_placements_student ON workplace_placements(student_id);
