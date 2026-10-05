"""Shared MailForge brand assets."""

from base64 import b64encode
from pathlib import Path


LOGO_PATH = Path(__file__).resolve().parents[1] / "assets" / "mailforge-favicon.png"
LOGO_DATA_URI = (
    "data:image/png;base64," + b64encode(LOGO_PATH.read_bytes()).decode("ascii")
)

