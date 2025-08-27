# main.py
# This file contains the backend logic for the student registration application.
# It uses the Flask web framework to create a simple API that listens for
# registration requests and adds the student data to a MySQL database.

from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
from mysql.connector import Error

# --- Configuration ---
# Database connection details.
# IMPORTANT: Replace these with your actual MySQL credentials.
DB_CONFIG = {
    'host': 'localhost',
    'database': 'student_registration_db',
    'user': 'root',       # <-- Replace with your user
    'password': 'Barcelona@1819' # <-- Replace with your password
}

# --- Flask App Initialization ---
# Initialize the Flask application.
app = Flask(__name__)
# Enable Cross-Origin Resource Sharing (CORS) to allow the frontend,
# which is served from a different origin, to communicate with this backend.
CORS(app)

# --- Database Connection Function ---
def create_db_connection():
    """Establishes a connection to the MySQL database."""
    connection = None
    try:
        # Attempt to connect to the database using the provided configuration.
        connection = mysql.connector.connect(**DB_CONFIG)
        print("MySQL Database connection successful")
    except Error as e:
        # If an error occurs during connection, print the error message.
        print(f"The error '{e}' occurred")
    return connection

# --- API Endpoint for Student Registration ---
@app.route('/register', methods=['POST'])
def register_student():
    """
    API endpoint to handle student registration.
    It expects a POST request with JSON data containing
    first_name, last_name, and email.
    """
    # Get the JSON data from the incoming request.
    data = request.get_json()
    first_name = data.get('first_name')
    last_name = data.get('last_name')
    email = data.get('email')

    # --- Input Validation ---
    # Basic validation to ensure all required fields are present.
    if not all([first_name, last_name, email]):
        return jsonify({'error': 'Missing required fields'}), 400

    # --- Database Interaction ---
    connection = create_db_connection()
    # If the connection fails, return a server error.
    if connection is None:
        return jsonify({'error': 'Could not connect to the database'}), 500

    cursor = connection.cursor()
    try:
        # The SQL query to insert a new student into the 'students' table.
        # Using placeholders (%s) is a security best practice to prevent SQL injection.
        query = "INSERT INTO students (first_name, last_name, email) VALUES (%s, %s, %s)"
        # The data to be inserted, passed as a tuple.
        student_data = (first_name, last_name, email)

        # Execute the query with the student data.
        cursor.execute(query, student_data)
        # Commit the transaction to make the changes permanent in the database.
        connection.commit()

        # Prepare a success response.
        response = {
            'status': 'success',
            'message': f'Student {first_name} {last_name} registered successfully!',
            'student_id': cursor.lastrowid # Get the ID of the newly inserted student.
        }
        return jsonify(response), 201 # 201 Created status code

    except Error as e:
        # If an error occurs (e.g., duplicate email), roll back the transaction.
        connection.rollback()
        # Return an error message.
        return jsonify({'error': f'Failed to register student. Error: {e}'}), 500

    finally:
        # --- Cleanup ---
        # Ensure the cursor and connection are closed, regardless of success or failure.
        if cursor:
            cursor.close()
        if connection.is_connected():
            connection.close()
            print("MySQL connection is closed")


# --- Main Execution Block ---
if __name__ == '__main__':
    # This block runs the Flask development server.
    # host='0.0.0.0' makes the server accessible from any IP address on the network.
    # port=5000 is the standard port for Flask development.
    # debug=True enables debug mode, which provides helpful error messages
    # and automatically reloads the server when code changes.
    app.run(host='0.0.0.0', port=5000, debug=True)
 
