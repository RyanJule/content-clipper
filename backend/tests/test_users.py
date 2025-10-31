def test_create_user(client):
    """Test user creation"""
    user_data = {
        "email": "test@example.com",
        "username": "testuser",
        "password": "testpassword123",
        "full_name": "Test User",
    }

    response = client.post("/api/v1/users/", json=user_data)
    assert response.status_code == 201

    data = response.json()
    assert data["email"] == user_data["email"]
    assert data["username"] == user_data["username"]
    assert "id" in data
    assert "hashed_password" not in data


def test_create_duplicate_user(client):
    """Test creating user with duplicate email"""
    user_data = {
        "email": "test@example.com",
        "username": "testuser",
        "password": "testpassword123",
    }

    client.post("/api/v1/users/", json=user_data)
    response = client.post("/api/v1/users/", json=user_data)

    assert response.status_code == 400
    assert "already registered" in response.json()["detail"].lower()


def test_get_user(client):
    """Test getting a user"""
    user_data = {
        "email": "test@example.com",
        "username": "testuser",
        "password": "testpassword123",
    }

    create_response = client.post("/api/v1/users/", json=user_data)
    user_id = create_response.json()["id"]

    response = client.get(f"/api/v1/users/{user_id}")
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == user_id
    assert data["email"] == user_data["email"]


def test_list_users(client):
    """Test listing users"""
    response = client.get("/api/v1/users/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
