from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.test.utils import override_settings
from django.urls import reverse

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "is_staff,is_superuser,is_active",
    [(True, False, True), (False, True, True), (False, False, False)],
)
@override_settings(DEBUG=True)
def test_demo_login_rejects_ineligible_existing_user_without_changes(
    client: Client,
    is_staff: bool,
    is_superuser: bool,
    is_active: bool,
) -> None:
    user_model = get_user_model()
    user = user_model.objects.create_user(
        username="demo",
        password="existing-password",
        is_staff=is_staff,
        is_superuser=is_superuser,
        is_active=is_active,
    )
    password_hash = user.password

    response = client.post(reverse("sample_app:demo-login"))

    user.refresh_from_db()
    assert response.status_code == 302
    assert response["Location"] == reverse("sample_app:login")
    assert user.password == password_hash
    assert client.session.get("_auth_user_id") is None


@override_settings(DEBUG=True)
def test_demo_login_creates_user_with_unusable_password(client: Client) -> None:
    response = client.post(reverse("sample_app:demo-login"))

    user = get_user_model().objects.get(username="demo")
    assert response.status_code == 302
    assert response["Location"] == reverse("sample_app:home")
    assert not user.has_usable_password()
    assert client.session.get("_auth_user_id") == str(user.pk)


@override_settings(DEBUG=True)
def test_demo_login_revokes_existing_usable_password(client: Client) -> None:
    user = get_user_model().objects.create_user(username="demo", password="legacy-password")

    response = client.post(reverse("sample_app:demo-login"))

    user.refresh_from_db()
    assert response.status_code == 302
    assert response["Location"] == reverse("sample_app:home")
    assert not user.has_usable_password()
    assert client.session.get("_auth_user_id") == str(user.pk)


@pytest.mark.parametrize("debug", [False, True])
def test_ordinary_login_rejects_demo_account_even_with_legacy_password(
    client: Client,
    debug: bool,
) -> None:
    user = get_user_model().objects.create_user(username="demo", password="demo")

    with override_settings(DEBUG=debug):
        response = client.post(
            reverse("sample_app:login"),
            {"username": "demo", "password": "demo"},
        )

    user.refresh_from_db()
    assert response.status_code == 200
    assert user.check_password("demo")
    assert client.session.get("_auth_user_id") is None


def test_demo_route_does_not_change_legacy_account_when_disabled(
    client: Client,
) -> None:
    user = get_user_model().objects.create_user(username="demo", password="demo")
    password_hash = user.password

    with override_settings(DEBUG=False):
        response = client.post(reverse("sample_app:demo-login"))

    user.refresh_from_db()
    assert response.status_code == 302
    assert user.password == password_hash


def test_normal_user_login_still_works(client: Client) -> None:
    user = get_user_model().objects.create_user(username="normal", password="safe-password")

    response = client.post(
        reverse("sample_app:login"),
        {"username": "normal", "password": "safe-password"},
    )

    assert response.status_code == 302
    assert response["Location"] == reverse("sample_app:home")
    assert client.session.get("_auth_user_id") == str(user.pk)


@override_settings(DEBUG=True)
def test_demo_login_requires_post_and_csrf() -> None:
    client = Client(enforce_csrf_checks=True)
    url = reverse("sample_app:demo-login")

    assert client.get(url).status_code == 405
    assert client.post(url).status_code == 403
    assert not get_user_model().objects.filter(username="demo").exists()

    login_page = client.get(reverse("sample_app:login"))
    assert b'action="/demo-login/"' in login_page.content
    token = client.cookies["csrftoken"].value
    response = client.post(url, {"csrfmiddlewaretoken": token})

    assert response.status_code == 302
    assert client.session.get("_auth_user_id") is not None


@override_settings(DEBUG=False)
def test_disabled_demo_login_has_no_control(client: Client) -> None:
    response = client.get(reverse("sample_app:login"))

    assert b'action="/demo-login/"' not in response.content
    assert b"You can also use demo login" not in response.content
