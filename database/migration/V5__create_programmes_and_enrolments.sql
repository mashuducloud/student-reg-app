-- V5__create_programmes_and_enrolments.sql

-- Clean up any partial tables from earlier failed runs (dev-safe).
DROP TABLE IF EXISTS enrolments;
DROP TABLE IF EXISTS programmes;

-- =========================================================
-- Programmes: master list of qualifications / programmes
-- =========================================================
CREATE TABLE programmes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    programme_code VARCHAR(50) NOT NULL,
    programme_name VARCHAR(255) NOT NULL,
    nqf_level TINYINT NULL,
    credits INT NULL,
    description TEXT NULL,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- =========================================================
-- Enrolments: link students (learners) to programmes
-- =========================================================
CREATE TABLE enrolments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    programme_id INT NOT NULL,

    enrolment_status ENUM('applied', 'enrolled', 'completed', 'withdrawn')
        NOT NULL DEFAULT 'applied',

    enrolment_date DATE NULL,
    completion_date DATE NULL,

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_enrolments_student
        FOREIGN KEY (student_id) REFERENCES students(id),

    CONSTRAINT fk_enrolments_programme
        FOREIGN KEY (programme_id) REFERENCES programmes(id)
) ENGINE=InnoDB;
