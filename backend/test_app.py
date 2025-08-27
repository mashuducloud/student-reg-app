# backend/test_app.py
# This file contains the automated tests for our Flask application.

import pytest
import json
from main import app # Import the Flask app instance from your main file

@pytest.fixture
def client():
    """
    This is a pytest "fixture". It sets up a test client for our Flask app.
    Fixtures are reusable setup functions for tests.
    """
    # Configure the app for testing. This disables error catching during
    # request handling, so you get better error reports when testing.
    app.config['TESTING'] = True
    
    # The 'with' block ensures that the client is properly set up and torn down.
    with app.test_client() as client:
        # 'yield' provides the test client to the test function.
        yield client

# --- Test Cases ---

def test_successful_registration(client):
    """
    GIVEN a Flask application configured for testing
    WHEN a POST request with valid student data is made to '/register'
    THEN check that the response is valid and indicates success (201 Created)
    """
    # 1. Prepare the mock student data
    mock_student = {
        "first_name": "Test",
        "last_name": "User",
        "email": "test.user@example.com"
    }

    # 2. Use the test client to send a POST request
    response = client.post('/register', 
                           data=json.dumps(mock_student),
                           content_type='application/json')

    # 3. Assert the results (check if the test passed or failed)
    # Check for a '201 Created' status code, which indicates success.
    assert response.status_code == 201
    
    # Parse the JSON response data
    response_data = json.loads(response.data)
    
    # Check if the success message is in the response
    assert 'status' in response_data
    assert response_data['status'] == 'success'
    assert 'registered successfully' in response_data['message']

def test_registration_with_missing_fields(client):
    """
    GIVEN a Flask application configured for testing
    WHEN a POST request with missing data is made to '/register'
    THEN check that the response is an error (400 Bad Request)
    """
    # 1. Prepare mock data with a missing field (e.g., no email)
    mock_student_incomplete = {
        "first_name": "Incomplete",
        "last_name": "User"
    }

    # 2. Send the POST request
    response = client.post('/register',
                           data=json.dumps(mock_student_incomplete),
                           content_type='application/json')

    # 3. Assert the results
    # Check for a '400 Bad Request' status code.
    assert response.status_code == 400
    
    # Parse the response data
    response_data = json.loads(response.data)
    
    # Check if the error message is correct
    assert 'error' in response_data
    assert response_data['error'] == 'Missing required fields'

