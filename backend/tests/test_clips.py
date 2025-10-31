def test_create_clip_invalid_media(client):
    """Test creating clip with invalid media ID"""
    clip_data = {"media_id": 999, "start_time": 0.0, "end_time": 10.0}

    response = client.post("/api/v1/clips/", json=clip_data)
    assert response.status_code == 400


def test_list_clips(client):
    """Test listing clips"""
    response = client.get("/api/v1/clips/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_clip_not_found(client):
    """Test getting non-existent clip"""
    response = client.get("/api/v1/clips/999")
    assert response.status_code == 404
