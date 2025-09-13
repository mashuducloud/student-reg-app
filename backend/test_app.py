import pytest
import json
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
        content_type="application/json"
    )
    assert response.status_code == 400
    assert b"required" in response.data


def test_register_success(monkeypatch, client):
    """Test /register endpoint with valid data (DB mocked)"""

    # mock DB connection and cursor
    class DummyCursor:
        def execute(self, *args, **kwargs): pass
        def close(self): pass

    class DummyConnection:
        def cursor(self): return DummyCursor()
        def commit(self): pass
        def close(self): pass
        def is_connected(self): return True

    monkeypatch.setattr("main.create_db_connection", lambda: DummyConnection())

    response = client.post(
        "/register",
        data=json.dumps({
            "first_name": "Jane",
            "last_name": "Doe",
            "email": "jane.doe@example.com"
        }),
        content_type="application/json"
    )

    assert response.status_code == 201
    assert b"Student registered successfully" in response.data


def test_create_db_connection(monkeypatch):
    """Directly test create_db_connection() with mocked mysql.connector"""

    class DummyConnection:
        def is_connected(self): return True

    class DummyConnector:
        @staticmethod
        def connect(**kwargs): return DummyConnection()

    # Patch mysql.connector inside main.py
    import main
    monkeypatch.setattr(main.mysql, "connector", DummyConnector)

    conn = create_db_connection()
    assert conn is not None
    assert conn.is_connected()