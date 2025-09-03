3-Tier Student Registration Web Application
This project is a classic 3-tier web application designed for student registration. It demonstrates a full-stack development workflow, including a frontend interface, a backend API, a relational database, automated testing, and observability with logging and tracing.

Architecture
The application is built using a decoupled 3-tier architecture, which separates concerns and improves scalability.

Presentation Tier (Frontend): A clean, responsive user interface built with HTML, Tailwind CSS, and vanilla JavaScript. This is what the user interacts with.

Logic Tier (Backend): A robust REST API built with Python and the Flask web framework. It handles business logic, validation, and communication with the database.

Data Tier (Database): A MySQL relational database to persistently store student registration data.

Features
Student Registration: A simple form to register new students with their first name, last name, and email.

Automated Backend Testing: Unit tests for the API endpoints using the pytest framework.

Observability: Integrated OpenTelemetry for structured logging and request tracing, providing deep insights into the application's behavior.

Local Version Control: The project is set up with a local Git repository to track all changes.

Project Structure
The project is organized into distinct folders for each tier, promoting a clean and maintainable codebase.

student-registration-app/
├── backend/
│   ├── venv/               # Python virtual environment
│   ├── main.py             # Main Flask application with logging/tracing
│   ├── test_app.py         # Pytest test file for the API
│   └── requirements.txt    # Python dependencies
│
├── database/
│   └── schema.sql          # SQL script to create the database and table
│
├── frontend/
│   └── index.html          # The HTML frontend interface
│
├── .gitignore              # Specifies files for Git to ignore
└── README.md               # Project documentation (this file)

Prerequisites
Before you begin, ensure you have the following installed on your local machine:

Python 3.8+

MySQL Server (including MySQL Workbench)

Visual Studio Code

Python Extension

Live Server Extension

Git

Setup and Installation Guide
Follow these steps to get the application running on your local machine.

1. Set Up the Database
Open MySQL Workbench and connect to your local MySQL server.

Go to File > Open SQL Script... and select the database/schema.sql file.

Execute the script by clicking the lightning bolt (⚡) icon. This will create the student_registration_db database and the students table.

2. Configure the Backend
Open a terminal in the project's root directory (student-registration-app/).

Navigate to the backend folder:

cd backend

Create and activate a Python virtual environment:

# Create the virtual environment
python -m venv venv

# Activate it (on Windows)
.\venv\Scripts\activate

Install the required Python packages:

pip install -r requirements.txt

Crucially, open backend/main.py and update the DB_CONFIG dictionary with your MySQL username and password.

3. Run the Application
You will need two terminals running simultaneously.

Terminal 1: Start the Backend Server
Ensure you are in the backend directory with your venv activated.

Run the Flask application:

python main.py

The server will start on http://localhost:5000. You will see OpenTelemetry logs and traces in this terminal. Leave this terminal running.

Terminal 2 (or VS Code UI): Launch the Frontend
In the VS Code file explorer, navigate to the frontend folder.

Right-click on index.html.

Select "Open with Live Server".

Your default browser will open with the registration form, and the application is now fully functional.

Running the Tests
To ensure the backend API is working correctly, you can run the automated tests.

Open a new terminal and navigate to the backend directory.

Activate the virtual environment (.\venv\Scripts\activate).

Run pytest:

pytest

The tests will execute, and you will see the results in the terminal.

Local Version Control with Git
This project is configured as a local Git repository.

To see the status of your changes:

git status

To save your work (commit process):

# 1. Stage all your changes for the next commit
git add .

# 2. Save the staged changes with a descriptive message
git commit -m "Your descriptive message here"

