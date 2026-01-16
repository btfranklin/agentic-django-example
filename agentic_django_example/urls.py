from __future__ import annotations

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("agents/", include("agentic_django.urls")),
    path("", include("sample_app.urls")),
]
