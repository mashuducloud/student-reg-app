-- V3: seed initial student data (example)

USE student_registration_db;

INSERT INTO students (first_name, last_name, email)
VALUES
    ('Alice',   'Smith',    'alice.smith@example.com'),
    ('Bob',     'Johnson',  'bob.johnson@example.com'),
    ('Charlie', 'Brown',    'charlie.brown@example.com');
