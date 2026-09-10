"""Configuration helpers: data directory and log level.

Precedence for the data directory: the ``MOECOG_DATA_DIR`` environment variable, then ``data_dir`` in
``~/.moecog/config.json`` (written by :func:`set_data_dir`), then ``~/moecog_data``. The environment variable
wins so that the same code runs on a laptop and on a cluster whose job scripts export the variable.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path

CONFIG_PATH = Path("~/.moecog/config.json").expanduser()
DEFAULT_DATA_DIR = Path("~/moecog_data").expanduser()

log = logging.getLogger("moecog")


def _load_config() -> dict:
    try:
        return json.loads(CONFIG_PATH.read_text())
    except (OSError, ValueError):
        return {}


def _save_config(cfg: dict) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(cfg, indent=1))


def get_data_dir() -> Path:
    """Directory under which loaders store downloads (``openneuro/``, ``dandi/``, ``hf/``, ...)."""
    env = os.environ.get("MOECOG_DATA_DIR")
    if env:
        return Path(env).expanduser()
    cfg = _load_config().get("data_dir")
    return Path(cfg).expanduser() if cfg else DEFAULT_DATA_DIR


def set_data_dir(path, persist: bool = True) -> Path:
    """Set the data directory for this process and, by default, for future ones.

    Parameters
    ----------
    path : str or Path
        Created if missing.
    persist : bool
        Also write it to ``~/.moecog/config.json``. The ``MOECOG_DATA_DIR`` environment variable still takes
        precedence when set.
    """
    path = Path(path).expanduser()
    path.mkdir(parents=True, exist_ok=True)
    os.environ["MOECOG_DATA_DIR"] = str(path)
    if persist:
        cfg = _load_config()
        cfg["data_dir"] = str(path)
        _save_config(cfg)
    return path


def set_log_level(level="INFO"):
    """Set the level of the ``moecog`` logger (``"DEBUG"``, ``"INFO"``, ``"WARNING"``, ``"ERROR"``)."""
    lvl = logging.getLevelName(level.upper()) if isinstance(level, str) else level
    log.setLevel(lvl)
    if not log.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(levelname)s %(name)s: %(message)s"))
        log.addHandler(handler)
    return log
