from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.test import Client


@pytest.fixture
def user(db: None) -> User:
    user_model = get_user_model()
    return user_model.objects.create_user(username="test-user", password="password")


@pytest.fixture
def client_logged_in(client: Client, user: User) -> Client:
    client.force_login(user)
    return client
