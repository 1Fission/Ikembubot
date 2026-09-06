"""
storage.py - a very simple "database" using a JSON file.
"""

import json
import os
import time

DATA_FILE = os.path.join(os.path.dirname(__file__), "settings.json")

DEFAULT_SETTINGS = {
    "enabled": True,
    "whitelist": [],
    "toggle_log": [],
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


def _ensure_defaults(entry: dict) -> dict:
    if "enabled" not in entry:
        entry["enabled"] = True
    if "whitelist" not in entry:
        entry["whitelist"] = []
    if "toggle_log" not in entry:
        entry["toggle_log"] = []
    return entry


def get_settings(chat_id: int) -> dict:
    data = _load_all()
    key = str(chat_id)
    if key not in data:
        data[key] = {"enabled": True, "whitelist": [], "toggle_log": []}
        _save_all(data)
    else:
        data[key] = _ensure_defaults(data[key])
    return data[key]


def set_enabled(chat_id: int, enabled: bool) -> None:
    data = _load_all()
    key = str(chat_id)
    if key not in data:
        data[key] = {"enabled": True, "whitelist": [], "toggle_log": []}
    data[key] = _ensure_defaults(data[key])
    data[key]["enabled"] = enabled
    _save_all(data)


def log_toggle_action(chat_id: int, actor_name: str, new_value: bool) -> None:
    data = _load_all()
    key = str(chat_id)
    if key not in data:
        data[key] = {"enabled": True, "whitelist": [], "toggle_log": []}
    data[key] = _ensure_defaults(data[key])

    entry = {
        "actor": actor_name,
        "new_value": new_value,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    data[key]["toggle_log"].append(entry)
    data[key]["toggle_log"] = data[key]["toggle_log"][-10:]
    _save_all(data)


def get_toggle_log(chat_id: int) -> list:
    return get_settings(chat_id)["toggle_log"]


def add_whitelist_domain(chat_id: int, domain: str) -> None:
    data = _load_all()
    key = str(chat_id)
    if key not in data:
        data[key] = {"enabled": True, "whitelist": [], "toggle_log": []}
    data[key] = _ensure_defaults(data[key])
    domain = domain.lower().strip()
    if domain not in data[key]["whitelist"]:
        data[key]["whitelist"].append(domain)
    _save_all(data)


def remove_whitelist_domain(chat_id: int, domain: str) -> None:
    data = _load_all()
    key = str(chat_id)
    if key not in data:
        data[key] = {"enabled": True, "whitelist": [], "toggle_log": []}
    data[key] = _ensure_defaults(data[key])
    domain = domain.lower().strip()
    if domain in data[key]["whitelist"]:
        data[key]["whitelist"].remove(domain)
    _save_all(data)
