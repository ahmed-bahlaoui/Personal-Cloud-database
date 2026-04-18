import sys
import uuid
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import app.main
import app.queries
import app.auth
import app.storage
import psycopg2
import pytest
from app.db import Base
from app.settings import DATABASE_URL
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker


@pytest.fixture()
def client(tmp_path: Path) -> TestClient:
    source_url = make_url(DATABASE_URL)
    test_database_name = f"cloud_storage_test_{uuid.uuid4().hex[:8]}"
    admin_database = source_url.set(database="postgres")
    test_database_url = source_url.set(database=test_database_name)
    storage_root = tmp_path / "storage"
    storage_root.mkdir(parents=True, exist_ok=True)

    admin_connection = psycopg2.connect(
        dbname=admin_database.database,
        user=admin_database.username,
        password=admin_database.password,
        host=admin_database.host,
        port=admin_database.port,
    )
    admin_connection.autocommit = True

    try:
        with admin_connection.cursor() as cursor:
            cursor.execute(f'CREATE DATABASE "{test_database_name}"')

        engine = create_engine(
            test_database_url.render_as_string(hide_password=False))
        TestingSessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
        Base.metadata.create_all(bind=engine)

        original_session_local = app.main.SessionLocal
        original_auth_session_local = app.auth.SessionLocal
        original_queries_session_local = app.queries.SessionLocal
        original_main_storage_root = app.main.STORAGE_ROOT
        original_storage_module_root = app.storage.STORAGE_ROOT
        app.main.SessionLocal = TestingSessionLocal
        app.auth.SessionLocal = TestingSessionLocal
        app.queries.SessionLocal = TestingSessionLocal
        app.main.STORAGE_ROOT = storage_root
        app.storage.STORAGE_ROOT = storage_root

        try:
            with TestClient(app.main.app) as test_client:
                yield test_client
        finally:
            app.main.SessionLocal = original_session_local
            app.auth.SessionLocal = original_auth_session_local
            app.queries.SessionLocal = original_queries_session_local
            app.main.STORAGE_ROOT = original_main_storage_root
            app.storage.STORAGE_ROOT = original_storage_module_root
            engine.dispose()

        with admin_connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT pg_terminate_backend(pid)
                FROM pg_stat_activity
                WHERE datname = %s AND pid <> pg_backend_pid()
                """,
                (test_database_name,),
            )
            cursor.execute(f'DROP DATABASE "{test_database_name}"')
    finally:
        admin_connection.close()


@pytest.fixture()
def register_and_login(client):
    def _register_and_login(
        username: str = "user1",
        email: str = "user1@example.com",
        password: str = "strongpass123",
    ) -> dict[str, str]:
        register_response = client.post(
            "/auth/register",
            json={
                "email": email,
                "username": username,
                "password": password,
            },
        )
        assert register_response.status_code == 201

        login_response = client.post(
            "/auth/login",
            data={"username": username, "password": password},
        )
        assert login_response.status_code == 200

        token = login_response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    return _register_and_login
