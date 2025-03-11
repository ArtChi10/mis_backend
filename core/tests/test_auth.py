import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()


@pytest.mark.django_db
def test_register_user():
    client = APIClient()
    response = client.post("/api/register/", {
        "username": "newuser",
        "email": "newuser@example.com",
        "password": "testpass",
        "role": "patient"
    }, format="json")

    assert response.status_code == 201
    assert User.objects.filter(username="newuser").exists()


@pytest.mark.django_db
def test_login_user():
    user = User.objects.create_user(username="testuser", password="testpass")
    client = APIClient()

    response = client.post("/api/login/", {
        "username": "testuser",
        "password": "testpass"
    }, format="json")

    assert response.status_code == 200
    assert "access" in response.data
    assert "refresh" in response.data
