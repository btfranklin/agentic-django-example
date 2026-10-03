from __future__ import annotations

import pytest
from django.contrib.auth.models import AbstractBaseUser
from django.test import Client
from django.urls import reverse

pytestmark = pytest.mark.django_db


def test_logout_control_uses_csrf_protected_post(user: AbstractBaseUser) -> None:
    client = Client(enforce_csrf_checks=True)
    client.force_login(user)
    url = reverse("sample_app:logout")

    home = client.get(reverse("sample_app:home"))
    assert b'action="/logout/"' in home.content
    assert b'href="/logout/"' not in home.content
    assert client.get(url).status_code == 405
    assert client.post(url).status_code == 403
    assert client.session.get("_auth_user_id") == str(user.pk)

    response = client.post(url, {"csrfmiddlewaretoken": client.cookies["csrftoken"].value})

    assert response.status_code == 302
    assert response["Location"] == reverse("sample_app:login")
    assert client.session.get("_auth_user_id") is None
    home = client.get(reverse("sample_app:home"))
    assert home.status_code == 302
    assert home["Location"].startswith(reverse("sample_app:login"))
