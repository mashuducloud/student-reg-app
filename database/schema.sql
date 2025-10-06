 -- SQL script to create the database and the students table.
-- Execute this in your MySQL server.

-- 1. Create the database
-- This command creates a new database named 'student_registration_db'.
-- The CHARACTER SET and COLLATE clauses ensure that the database can store
-- a wide range of characters, which is good practice for web applications.
CREATE DATABASE IF NOT EXISTS student_registration_db
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

-- 2. Switch to the newly created database
-- This command sets the current database context, so all subsequent commands
-- will apply to 'student_registration_db'.
USE student_registration_db;

-- 3. Create the students table
-- This table will store the registration information for each student.
CREATE TABLE IF NOT EXISTS students (
    -- 'id' is the primary key, uniquely identifying each student record.
    -- It's an INT (integer), set to NOT NULL because it must have a value.
    -- AUTO_INCREMENT means MySQL will automatically assign a new, unique ID
    -- for each new record.
    id INT NOT NULL AUTO_INCREMENT,

    -- 'first_name' stores the student's first name.
    -- VARCHAR(100) allows for strings up to 100 characters.
    -- It's set to NOT NULL as this is a required field.
    first_name VARCHAR(100) NOT NULL,

    -- 'last_name' stores the student's last name.
    -- VARCHAR(100) allows for strings up to 100 characters.
    -- NOT NULL ensures this field is always filled.
    last_name VARCHAR(100) NOT NULL,

    -- 'email' stores the student's email address.
    -- VARCHAR(150) provides ample space for longer email addresses.
    -- NOT NULL and UNIQUE ensure every student has a distinct email.
    email VARCHAR(150) NOT NULL UNIQUE,

    -- 'registration_date' stores the timestamp of when the registration occurred.
    -- TIMESTAMP is a data type for date and time.
    -- DEFAULT CURRENT_TIMESTAMP automatically sets the registration time
    -- to the current time when a new record is created.
    registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- This sets the 'id' column as the primary key for the table.
    PRIMARY KEY (id)
);

-- 4. (Optional) Describe the table structure
-- You can run this command after creation to verify the table schema.
DESCRIBE students;
