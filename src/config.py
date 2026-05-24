"""
Configuration manager for KOL Matcher.

Manages DATA_CSV_PATH from .env with memory caching.
All modules should read the data file path through this module.
"""

import datetime
import shutil
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
ENV_FILE = BASE_DIR / ".env"
DEFAULT_CSV_PATH = "data/influencers.csv"
_BACKUP_DIR = BASE_DIR / "data" / "backups"
_MAX_BACKUPS = 10

# In-memory cache for the current data path to avoid reading .env on every request
_current_path: Path | None = None


def _read_env() -> dict:
    """Read .env file into a dict."""
    config = {}
    if ENV_FILE.exists():
        with open(ENV_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and "=" in line and not line.startswith("#"):
                    key, val = line.split("=", 1)
                    config[key.strip()] = val.strip()
    return config


def _write_env(config: dict):
    """Write dict back to .env file."""
    lines = []
    for key, val in sorted(config.items()):
        lines.append(f"{key}={val}")
    with open(ENV_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def get_data_path() -> Path:
    """Return the absolute Path of the current data CSV file."""
    global _current_path
    if _current_path is not None:
        return _current_path

    env = _read_env()
    path_str = env.get("DATA_CSV_PATH", DEFAULT_CSV_PATH)
    path = Path(path_str)
    if not path.is_absolute():
        path = BASE_DIR / path
    _current_path = path.resolve()
    return _current_path


def set_data_path(path: str | Path):
    """Update the data file path in memory and .env."""
    global _current_path
    path_obj = Path(path).resolve()
    _current_path = path_obj

    # Store as relative path if under BASE_DIR, otherwise absolute
    try:
        rel = path_obj.relative_to(BASE_DIR.resolve())
        save_val = str(rel).replace("\\", "/")
    except ValueError:
        save_val = str(path_obj).replace("\\", "/")

    env = _read_env()
    env["DATA_CSV_PATH"] = save_val
    _write_env(env)


def get_data_info() -> dict:
    """Return current data file metadata: name, record count, last modified time."""
    path = get_data_path()
    if not path.exists():
        return {"file_name": path.name, "record_count": 0, "last_modified": None}

    # Delayed import to avoid circular dependency with csv_loader
    from csv_loader import CSVLoader

    loader = CSVLoader(str(path))
    try:
        df = loader.load()
        count = len(df)
    except Exception:
        count = 0

    mtime = datetime.datetime.fromtimestamp(path.stat().st_mtime)
    return {
        "file_name": path.name,
        "record_count": count,
        "last_modified": mtime.strftime("%Y-%m-%d %H:%M"),
    }


def backup_current() -> Path | None:
    """Backup the current data file and return the backup path."""
    path = get_data_path()
    if not path.exists():
        return None

    _BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = _BACKUP_DIR / f"{path.stem}_{timestamp}{path.suffix}"
    shutil.copy2(path, backup_path)

    # Clean up old backups, keep only the most recent _MAX_BACKUPS
    backups = sorted(
        _BACKUP_DIR.glob(f"{path.stem}_*{path.suffix}"),
        key=lambda p: p.stat().st_mtime,
    )
    if len(backups) > _MAX_BACKUPS:
        for old in backups[:-_MAX_BACKUPS]:
            old.unlink(missing_ok=True)

    return backup_path


if __name__ == "__main__":
    print(f"BASE_DIR: {BASE_DIR}")
    print(f"DATA_CSV_PATH: {get_data_path()}")
    print(f"DATA_INFO: {get_data_info()}")
