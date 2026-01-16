#!/usr/bin/env python
from __future__ import annotations

import os
import sys
from pathlib import Path


def main() -> None:
    base_dir = Path(__file__).resolve().parent
    apps_dir = base_dir / "apps"
    if str(apps_dir) not in sys.path:
        sys.path.insert(0, str(apps_dir))

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "agentic_django_example.settings")
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
