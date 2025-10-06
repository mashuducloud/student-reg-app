import json

import pytest
from main import app, create_db_connection


@pytest.fixture
def client():
    """Flask test client fixture"""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_home(client):
    """Test home endpoint returns 200"""
    response = client.get("/")
    assert response.status_code == 200
    assert b"Student Registration API is running" in response.data


def test_register_missing_fields(client):
    """Test /register endpoint with missing data"""
    response = client.post(
        "/register",
        data=json.dumps({"first_name": "John"}),  # missing last_name, email
        content_type="application/json",
    )
    assert response.status_code == 400
    assert b"required" in response.data


def test_register_success(monkeypatch, client):
    """Test /register endpoint with valid data (DB mocked)"""

    class DummyCursor:
        def execute(self, *_args, **_):
            pass

        def close(self):
            pass

    class DummyConnection:
        def cursor(self):
            return DummyCursor()

        def commit(self):
            pass

        def close(self):
            pass

        def is_connected(self):
            return True

    monkeypatch.setattr("main.create_db_connection", lambda: DummyConnection())

    response = client.post(
        "/register",
        data=json.dumps({"first_name": "Jane", "last_name": "Doe", "email": "jane.doe@example.com"}),
        content_type="application/json",
    )

    assert response.status_code == 201
    assert b"Student registered successfully" in response.data


def test_register_db_failure(monkeypatch, client):
    """Test /register endpoint when DB connection fails"""

    # Force create_db_connection() to return None
    monkeypatch.setattr("main.create_db_connection", lambda: None)

    response = client.post(
        "/register",
        data=json.dumps({"first_name": "Fail", "last_name": "Case", "email": "fail@example.com"}),
        content_type="application/json",
    )

    assert response.status_code == 500
    assert b"Failed to register student" in response.data


def test_create_db_connection_success(monkeypatch):
    """Directly test create_db_connection() success"""

    class DummyConnection:
        def is_connected(self):
            return True

    class DummyConnector:
        @staticmethod
        def connect(**_):
            return DummyConnection()

    import main

    monkeypatch.setattr(main.mysql, "connector", DummyConnector)

    conn = create_db_connection()
    assert conn is not None
    assert conn.is_connected()


def test_create_db_connection_failure(monkeypatch):
    """Directly test create_db_connection() failure"""

    class DummyConnector:
        @staticmethod
        def connect(**_):
            raise Exception("DB connection failed")

    import main

    monkeypatch.setattr(main.mysql, "connector", DummyConnector)

    conn = create_db_connection()
    assert conn is None
