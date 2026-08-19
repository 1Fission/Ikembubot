"""
storage.py - a very simple "database" using a JSON file.

We keep one settings entry per group (per chat_id):
    {
        "-100123456789": {
            "enabled": true,
            "whitelist": ["youtube.com", "twitter.com"]
        }
    }

This is intentionally simple (no real database) so it's easy to understand
and costs nothing to run.
"""

import json
import os

DATA_FILE = os.path.join(os.path.dirname(__file__), "settings.json")

DEFAULT_SETTINGS = {
    "enabled": True,
    "whitelist": [],
}


def _load_all() -> dict:
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}


def _save_all(data: dict) -> None:
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def get_settings(chat_id: int) -> dict:
    data = _load_all()
    key = str(chat_id)
    if key not in data:
        data[key] = dict(DEFAULT_SETTINGS)
        _save_all(data)
    return data[key]


def set_enabled(chat_id: int, enabled: bool) -> None:
    data = _load_all()
    key = str(chat_id)
    if key not in data:
        data[key] = dict(DEFAULT_SETTINGS)
    data[key]["enabled"] = enabled
    _save_all(data)


def add_whitelist_domain(chat_id: int, domain: str) -> None:
    data = _load_all()
    key = str(chat_id)
    if key not in data:
        data[key] = dict(DEFAULT_SETTINGS)
    domain = domain.lower().strip()
    if domain not in data[key]["whitelist"]:
        data[key]["whitelist"].append(domain)
    _save_all(data)


def remove_whitelist_domain(chat_id: int, domain: str) -> None:
    data = _load_all()
    key = str(chat_id)
    if key not in data:
        data[key] = dict(DEFAULT_SETTINGS)
    domain = domain.lower().strip()
    if domain in data[key]["whitelist"]:
        data[key]["whitelist"].remove(domain)
    _save_all(data)
