import json

import main
import pytest
from db import create_db_connection
from main import app
from repositories.students_repository import EmailAlreadyExistsError


@pytest.fixture
def client():
    """Flask test client fixture"""
    app.config["TESTING"] = True
    app.config["BYPASS_AUTH"] = True  # bypass auth during tests
    with app.test_client() as client:
        yield client


def test_home(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Student Registration API is running" in response.data


def test_register_missing_fields(client):
    response = client.post(
        "/register",
        data=json.dumps({"first_name": "John"}),
        content_type="application/json",
    )
    assert response.status_code == 400
    assert b"required" in response.data


def test_register_success(monkeypatch, client):
    """Test /register endpoint with valid data (repository mocked)"""

    def fake_register_student(first_name, last_name, email):
        assert first_name == "Jane"
        assert last_name == "Doe"
        assert email == "jane.doe@example.com"
        return 123

    monkeypatch.setattr(main, "register_student", fake_register_student)

    response = client.post(
        "/register",
        data=json.dumps(
            {
                "first_name": "Jane",
                "last_name": "Doe",
                "email": "jane.doe@example.com",
            }
        ),
        content_type="application/json",
    )

    assert response.status_code == 201

    body = response.get_json()
    assert body["id"] == 123
    assert body["message"] == "Student registered successfully"


def test_register_db_failure(monkeypatch, client):
    def fake_register_student(*_args, **_kwargs):
        raise Exception("DB or repo failure")

    monkeypatch.setattr(main, "register_student", fake_register_student)

    response = client.post(
        "/register",
        data=json.dumps(
            {
                "first_name": "Fail",
                "last_name": "Case",
                "email": "fail@example.com",
            }
        ),
        content_type="application/json",
    )

    assert response.status_code == 500
    assert b"Failed to register student" in response.data


def test_register_duplicate_email(monkeypatch, client):
    def fake_register_student(*_args, **_kwargs):
        raise EmailAlreadyExistsError("Email already exists")

    monkeypatch.setattr(main, "register_student", fake_register_student)

    response = client.post(
        "/register",
        data=json.dumps(
            {
                "first_name": "Jane",
                "last_name": "Doe",
                "email": "jane.doe@example.com",
            }
        ),
        content_type="application/json",
    )

    assert response.status_code == 409
    assert b"Email already exists" in response.data


def test_create_db_connection_success(monkeypatch):
    class DummyConnection:
        def is_connected(self):
            return True

    def fake_connect(**_kwargs):
        return DummyConnection()

    monkeypatch.setattr("db.mysql.connector.connect", fake_connect)

    conn = create_db_connection()
    assert conn is not None
    assert conn.is_connected()


def test_create_db_connection_failure(monkeypatch):
    def fake_connect(**_kwargs):
        raise Exception("DB connection failed")

    monkeypatch.setattr("db.mysql.connector.connect", fake_connect)

    conn = create_db_connection()
    assert conn is None
