"""Utility to synchronise README.md version strings with config values.

Usage (run from repository root):

    python tools/update_readme_version.py

The script reads ``config.APP_VERSION`` and ``APP_VERSION_DISPLAY`` and
performs an in-place update of the following patterns in README.md:

* the title line starting with
  ``# 🚗 Vehicle Management System — v...``
* any occurrence of the packaged exe name ``VehicleManagement_vX.Y.Z.exe``

Additional replacements can easily be added if your documentation contains
more hard‑coded version numbers.

The file is overwritten; consider running this as part of your release
pipeline before committing the updated README.
"""
import re
from pathlib import Path
import sys, os

# make sure root is on sys.path when running from tools/
root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if root not in sys.path:
    sys.path.insert(0, root)

from config import APP_VERSION, APP_VERSION_DISPLAY

README = Path("README.md")

if not README.exists():
    raise FileNotFoundError("README.md not found in repository root")

text = README.read_text(encoding="utf-8")

# update header line
text = re.sub(
    r"^# 🚗 Vehicle Management System — v[0-9\.]+",
    f"# 🚗 Vehicle Management System — v{APP_VERSION}",
    text,
    flags=re.MULTILINE,
)

# update exe filename reference
text = re.sub(
    r"VehicleManagement_v[0-9\.]+\.exe",
    f"VehicleManagement_v{APP_VERSION}.exe",
    text,
)

# (future replacements could go here)

README.write_text(text, encoding="utf-8")
print(f"README.md synchronised to {APP_VERSION_DISPLAY}")
