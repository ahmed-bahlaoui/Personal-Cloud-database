def test_register_creates_user(client):
    response = client.post(
        "/auth/register",
        json={
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "strongpass123",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "newuser@example.com"
    assert body["username"] == "newuser"
    assert "password_hash" not in body


def test_register_rejects_duplicate_username_or_email(client):
    payload = {
        "email": "duplicate@example.com",
        "username": "duplicate_user",
        "password": "strongpass123",
    }

    first_response = client.post("/auth/register", json=payload)
    second_response = client.post("/auth/register", json=payload)

    assert first_response.status_code == 201
    assert second_response.status_code == 409
    assert second_response.json()["detail"] == (
        "A user with this username or email already exists"
    )


def test_login_returns_access_token_for_valid_credentials(client):
    client.post(
        "/auth/register",
        json={
            "email": "loginuser@example.com",
            "username": "loginuser",
            "password": "strongpass123",
        },
    )

    response = client.post(
        "/auth/login",
        data={"username": "loginuser", "password": "strongpass123"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert isinstance(body["access_token"], str)
    assert body["access_token"]


def test_login_rejects_invalid_credentials(client):
    client.post(
        "/auth/register",
        json={
            "email": "wrongpass@example.com",
            "username": "wrongpass",
            "password": "strongpass123",
        },
    )

    response = client.post(
        "/auth/login",
        data={"username": "wrongpass", "password": "badpass123"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect username or password"
