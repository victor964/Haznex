#!/usr/bin/env python
"""
Reliable collectstatic for Railway.

manage.py collectstatic can report "0 static files copied" while skipping work.
This script uses the same code path that successfully copies all app static files.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "vhbridge.settings")

import django  # noqa: E402

django.setup()

from django.contrib.staticfiles.management.commands.collectstatic import Command  # noqa: E402
from django.core.management.base import OutputWrapper  # noqa: E402


def main() -> None:
    static_root = BACKEND_DIR / "staticfiles"
    static_root.mkdir(parents=True, exist_ok=True)

    cmd = Command(
        stdout=OutputWrapper(sys.stdout),
        stderr=OutputWrapper(sys.stderr),
    )
    cmd.run_from_argv(
        [
            "manage.py",
            "collectstatic",
            "--noinput",
            "--clear",
            "-v",
            "1",
        ]
    )

    count = sum(1 for _ in static_root.rglob("*") if _.is_file())
    print(f"Verified {count} files in {static_root}")
    if count == 0:
        print("ERROR: collectstatic finished but staticfiles/ is empty", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
