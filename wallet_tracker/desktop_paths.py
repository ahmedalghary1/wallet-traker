import os
import sys
from pathlib import Path


APP_DIR_NAME = "Wallet Tracker"


def env_flag(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def is_frozen():
    return bool(getattr(sys, "frozen", False))


def is_desktop_mode():
    return env_flag("DESKTOP_LOCAL_MODE") or is_frozen()


def resource_root():
    if is_frozen() and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent.parent


def default_data_dir():
    explicit_dir = os.getenv("WALLET_TRACKER_DATA_DIR")
    if explicit_dir:
        return Path(explicit_dir).expanduser()

    if os.name == "nt":
        base_dir = os.getenv("LOCALAPPDATA") or os.getenv("APPDATA")
        if base_dir:
            return Path(base_dir) / APP_DIR_NAME
        return Path.home() / "AppData" / "Local" / APP_DIR_NAME

    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / APP_DIR_NAME

    xdg_data_home = os.getenv("XDG_DATA_HOME")
    if xdg_data_home:
        return Path(xdg_data_home) / "wallet-tracker"
    return Path.home() / ".local" / "share" / "wallet-tracker"


def app_data_dir():
    data_dir = default_data_dir()
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def ensure_child_dir(parent, name):
    child = parent / name
    child.mkdir(parents=True, exist_ok=True)
    return child
