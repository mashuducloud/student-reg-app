USE student_registration_db;

DROP VIEW IF EXISTS v_students_basic;

CREATE VIEW v_students_basic AS
SELECT id, first_name, last_name, email, registration_date
FROM students;
