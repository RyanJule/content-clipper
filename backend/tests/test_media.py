import io


def test_upload_media_no_file(client):
    """Test media upload without file"""
    response = client.post("/api/v1/media/upload")
    assert response.status_code == 422


def test_list_media(client):
    """Test listing media"""
    response = client.get("/api/v1/media/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_media_not_found(client):
    """Test getting non-existent media"""
    response = client.get("/api/v1/media/999")
    assert response.status_code == 404
