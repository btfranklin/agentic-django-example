from __future__ import annotations

from django.contrib.auth.forms import AuthenticationForm


class SampleAuthenticationForm(AuthenticationForm):
    def clean(self) -> dict[str, object]:
        username = self.cleaned_data.get("username")
        if username == "demo":
            raise self.get_invalid_login_error()
        return super().clean()
