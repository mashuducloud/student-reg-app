USE student_registration_db;

-- =========================================================
-- Assessments table
-- Stores formative/summative assessments and moderation results
-- =========================================================

CREATE TABLE IF NOT EXISTS assessments (
    id INT AUTO_INCREMENT PRIMARY KEY,

    student_id INT NOT NULL,
    programme_id INT NOT NULL,

    assessment_type ENUM('Formative', 'Summative') NOT NULL,
    assessment_name VARCHAR(255) NOT NULL,

    assessment_date DATE NULL,

    score DECIMAL(10,2) NULL,
    max_score DECIMAL(10,2) NULL,

    result VARCHAR(50) NULL,              -- e.g. Competent / Not Yet Competent / Pending
    moderation_outcome VARCHAR(255) NULL, -- e.g. Confirmed / Adjusted / Rejected

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_assessments_student
        FOREIGN KEY (student_id) REFERENCES students(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_assessments_programme
        FOREIGN KEY (programme_id) REFERENCES programmes(id)
        ON DELETE CASCADE
);

-- Helpful indexes
CREATE INDEX idx_assessments_student ON assessments(student_id);
CREATE INDEX idx_assessments_programme ON assessments(programme_id);
CREATE INDEX idx_assessments_type ON assessments(assessment_type);
