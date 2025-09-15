import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
def test_create_user():
    user = User.objects.create_user(username="testuser", password="password123")
    assert user.username == "testuser"
    assert user.check_password("password123") is True


@pytest.mark.django_db
def test_str_user():
    user = User.objects.create_user(username="struser", password="password123")
    assert str(user) == user.username
