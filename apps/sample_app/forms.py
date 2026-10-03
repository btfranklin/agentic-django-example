from __future__ import annotations

from typing import Any

from django.contrib.auth.forms import AuthenticationForm


class SampleAuthenticationForm(AuthenticationForm):
    def clean(self) -> dict[str, Any]:
        username = self.cleaned_data.get("username")
        if username == "demo":
            raise self.get_invalid_login_error()
        return super().clean()
