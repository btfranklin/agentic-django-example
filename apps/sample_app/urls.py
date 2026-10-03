from __future__ import annotations

from django.contrib.auth import views as auth_views
from django.urls import path

from sample_app import forms, views

app_name = "sample_app"

urlpatterns = [
    path("", views.home, name="home"),
    path("demo-login/", views.demo_login, name="demo-login"),
    path("reset/", views.reset_session, name="reset"),
    path(
        "login/",
        auth_views.LoginView.as_view(
            template_name="sample_app/login.html",
            authentication_form=forms.SampleAuthenticationForm,
        ),
        name="login",
    ),
    path(
        "logout/",
        auth_views.LogoutView.as_view(next_page="sample_app:login"),
        name="logout",
    ),
]
