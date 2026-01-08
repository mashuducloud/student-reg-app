-- V9__create_documents.sql
USE student_registration_db;

CREATE TABLE IF NOT EXISTS documents (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,

    document_name VARCHAR(255) NOT NULL,
    document_type VARCHAR(100),
    file_path     VARCHAR(500) NOT NULL,
    uploaded_by   VARCHAR(255),

    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_documents_student
      FOREIGN KEY (student_id) REFERENCES students(id)
      ON DELETE CASCADE
);

CREATE INDEX idx_documents_student ON documents(student_id);
