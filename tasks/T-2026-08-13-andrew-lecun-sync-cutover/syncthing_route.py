#!/usr/bin/env python3
"""Inspect and reversibly move one Syncthing localhost route via granular REST."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

HOME = Path("/home/ubuntu")
API_ROOT = "http://127.0.0.1:8384"
LOCALHOST_ROUTE = "tcp://127.0.0.1:22001"
PHILIP_NAME = "philip"
LECUN_NAME = "lecun"
LECUN_DIRECT = "tcp://192.168.196.176:22000"


def config_path() -> Path:
    candidates = (
        HOME / ".local/state/syncthing/config.xml",
        HOME / ".config/syncthing/config.xml",
    )
    for path in candidates:
        if path.is_file():
            return path
    raise FileNotFoundError("Syncthing config.xml was not found in known locations")


def api_key_and_config_devices() -> tuple[str, dict[str, str]]:
    root = ET.parse(config_path()).getroot()
    api_element = root.find("./gui/apikey")
    if api_element is None or not (api_element.text or "").strip():
        raise RuntimeError("Syncthing API key is absent")
    devices: dict[str, str] = {}
    for element in root.findall("./device"):
        name = element.get("name")
        device_id = element.get("id")
        if name and device_id:
            if name in devices:
                raise RuntimeError(f"duplicate device name in config.xml: {name}")
            devices[name] = device_id
    return (api_element.text or "").strip(), devices


def request_json(api_key: str, path: str, method: str = "GET", payload: Any = None) -> Any:
    body = None if payload is None else json.dumps(payload, sort_keys=True).encode("utf-8")
    request = urllib.request.Request(
        API_ROOT + path,
        data=body,
        method=method,
        headers={"X-API-Key": api_key, "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            raw = response.read()
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"Syncthing REST {method} {path} failed with HTTP {exc.code}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Syncthing REST {method} {path} was unreachable: {exc.reason}") from exc
    return json.loads(raw) if raw else {}


def canonical_hash(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def without_addresses(device: dict[str, Any]) -> dict[str, Any]:
    result = json.loads(json.dumps(device))
    result.pop("addresses", None)
    return result


def contains_secret_field(value: Any) -> bool:
    if isinstance(value, dict):
        for key, nested in value.items():
            lowered = str(key).lower().replace("_", "").replace("-", "")
            if any(token in lowered for token in ("apikey", "password", "token", "secret")):
                return True
            if contains_secret_field(nested):
                return True
    elif isinstance(value, list):
        return any(contains_secret_field(item) for item in value)
    return False


def safe_device(device: dict[str, Any]) -> dict[str, Any]:
    return {
        "deviceID": device.get("deviceID"),
        "name": device.get("name"),
        "addresses": list(device.get("addresses") or []),
        "paused": device.get("paused"),
        "object_sha256": canonical_hash(device),
        "non_address_sha256": canonical_hash(without_addresses(device)),
    }


def route_state(philip: dict[str, Any], lecun: dict[str, Any], devices: list[dict[str, Any]]) -> str:
    holders = [
        device.get("name") or device.get("deviceID")
        for device in devices
        if LOCALHOST_ROUTE in (device.get("addresses") or [])
    ]
    if len(holders) == 0:
        return "missing"
    if len(holders) > 1:
        return "duplicate"
    if LOCALHOST_ROUTE in (philip.get("addresses") or []) and holders == [philip.get("name")]:
        return "philip_only"
    if LOCALHOST_ROUTE in (lecun.get("addresses") or []) and holders == [lecun.get("name")]:
        return "lecun_only"
    return "unexpected"


def client_state() -> tuple[str, dict[str, str], list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    api_key, config_devices = api_key_and_config_devices()
    if PHILIP_NAME not in config_devices or LECUN_NAME not in config_devices:
        raise RuntimeError("philip or lecun device name is missing from config.xml")
    devices = request_json(api_key, "/rest/config/devices")
    if not isinstance(devices, list):
        raise RuntimeError("granular devices endpoint did not return a list")
    by_id = {device.get("deviceID"): device for device in devices}
    try:
        philip = by_id[config_devices[PHILIP_NAME]]
        lecun = by_id[config_devices[LECUN_NAME]]
    except KeyError as exc:
        raise RuntimeError("philip or lecun granular device object is missing") from exc
    return api_key, config_devices, devices, philip, lecun


def inspect() -> dict[str, Any]:
    api_key, config_devices, devices, philip, lecun = client_state()
    version = request_json(api_key, "/rest/system/version")
    restart = request_json(api_key, "/rest/config/restart-required")
    options = request_json(api_key, "/rest/config/options")
    folders = request_json(api_key, "/rest/config/folders")
    connections = request_json(api_key, "/rest/system/connections").get("connections", {})
    holders = [
        {"name": device.get("name"), "deviceID": device.get("deviceID")}
        for device in devices
        if LOCALHOST_ROUTE in (device.get("addresses") or [])
    ]
    folder_summary = [
        {
            "id": folder.get("id"),
            "label": folder.get("label"),
            "device_ids": sorted(
                item.get("deviceID") for item in (folder.get("devices") or []) if item.get("deviceID")
            ),
            "object_sha256": canonical_hash(folder),
        }
        for folder in folders
    ]
    target_connections = {}
    for name in (PHILIP_NAME, LECUN_NAME):
        device_id = config_devices[name]
        connection = connections.get(device_id) or {}
        target_connections[name] = {
            "deviceID": device_id,
            "connected": bool(connection.get("connected")),
            "address": connection.get("address"),
            "type": connection.get("type"),
        }
    return {
        "version": version.get("version"),
        "granular_devices_endpoint": True,
        "restart_required": bool(restart.get("requiresRestart")),
        "options": {
            "global_announce_enabled": options.get("globalAnnounceEnabled"),
            "relays_enabled": options.get("relaysEnabled"),
        },
        "device_count": len(devices),
        "devices": {PHILIP_NAME: safe_device(philip), LECUN_NAME: safe_device(lecun)},
        "localhost_route": {
            "address": LOCALHOST_ROUTE,
            "state": route_state(philip, lecun, devices),
            "holders": holders,
        },
        "lecun_direct_present": LECUN_DIRECT in (lecun.get("addresses") or []),
        "folders": folder_summary,
        "connections": target_connections,
    }


def secure_write_json(path: Path, value: Any) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    descriptor = os.open(path, flags, 0o600)
    try:
        data = (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")
        os.write(descriptor, data)
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def backup(backup_dir: Path) -> dict[str, Any]:
    if not backup_dir.is_dir() or stat.S_IMODE(backup_dir.stat().st_mode) != 0o700:
        raise RuntimeError("backup directory must already exist with mode 700")
    _api_key, _config_devices, _devices, philip, lecun = client_state()
    if contains_secret_field(philip) or contains_secret_field(lecun):
        raise RuntimeError("device object contains a secret-like field; refusing to persist")
    outputs = {}
    for name, device in ((PHILIP_NAME, philip), (LECUN_NAME, lecun)):
        path = backup_dir / f"syncthing-device-{name}.json"
        secure_write_json(path, device)
        outputs[name] = {"path": str(path), "mode": "600", "sha256": canonical_hash(device)}
    return {"backup": outputs}


def load_backup(backup_dir: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    values = []
    for name in (PHILIP_NAME, LECUN_NAME):
        path = backup_dir / f"syncthing-device-{name}.json"
        if stat.S_IMODE(path.stat().st_mode) != 0o600:
            raise RuntimeError(f"backup device object mode is not 600: {path}")
        value = json.loads(path.read_text(encoding="utf-8"))
        if contains_secret_field(value):
            raise RuntimeError(f"backup device object contains a secret-like field: {path}")
        values.append(value)
    return values[0], values[1]


def put_device(api_key: str, device: dict[str, Any]) -> None:
    device_id = device.get("deviceID")
    if not device_id:
        raise RuntimeError("device object has no deviceID")
    path = "/rest/config/devices/" + urllib.parse.quote(str(device_id), safe="")
    request_json(api_key, path, method="PUT", payload=device)


def move_to_lecun(backup_dir: Path) -> dict[str, Any]:
    backup_philip, backup_lecun = load_backup(backup_dir)
    api_key, _ids, devices, philip, lecun = client_state()
    if canonical_hash(philip) != canonical_hash(backup_philip) or canonical_hash(lecun) != canonical_hash(backup_lecun):
        raise RuntimeError("live target device objects no longer match the backup input")
    if route_state(philip, lecun, devices) != "philip_only":
        raise RuntimeError("localhost route is not in the required philip_only start state")
    before_non_address = {
        PHILIP_NAME: canonical_hash(without_addresses(philip)),
        LECUN_NAME: canonical_hash(without_addresses(lecun)),
    }
    changed_philip = json.loads(json.dumps(philip))
    changed_lecun = json.loads(json.dumps(lecun))
    changed_philip["addresses"] = [
        address for address in (changed_philip.get("addresses") or []) if address != LOCALHOST_ROUTE
    ]
    changed_lecun["addresses"] = list(changed_lecun.get("addresses") or []) + [LOCALHOST_ROUTE]
    try:
        put_device(api_key, changed_philip)
        put_device(api_key, changed_lecun)
    except Exception:
        put_device(api_key, backup_philip)
        put_device(api_key, backup_lecun)
        raise
    after = inspect()
    if after["localhost_route"]["state"] != "lecun_only" or after["restart_required"]:
        put_device(api_key, backup_philip)
        put_device(api_key, backup_lecun)
        raise RuntimeError("post-change route or restart-required gate failed; device objects restored")
    for name in (PHILIP_NAME, LECUN_NAME):
        if after["devices"][name]["non_address_sha256"] != before_non_address[name]:
            put_device(api_key, backup_philip)
            put_device(api_key, backup_lecun)
            raise RuntimeError("non-address device field changed; device objects restored")
    return {"action": "move_to_lecun", "result": "PASS", "state": after}


def restore(backup_dir: Path) -> dict[str, Any]:
    philip, lecun = load_backup(backup_dir)
    api_key, _ids, _devices, _live_philip, _live_lecun = client_state()
    put_device(api_key, philip)
    put_device(api_key, lecun)
    after = inspect()
    if after["localhost_route"]["state"] != "philip_only" or after["restart_required"]:
        raise RuntimeError("restored device route did not return to philip_only without restart")
    return {"action": "restore", "result": "PASS", "state": after}


def self_test() -> tuple[dict[str, bool], bool]:
    philip = {"deviceID": "P", "name": "philip", "addresses": [LOCALHOST_ROUTE, "dynamic"]}
    lecun = {"deviceID": "L", "name": "lecun", "addresses": [LECUN_DIRECT, "dynamic"]}
    duplicate = json.loads(json.dumps(lecun))
    duplicate["addresses"].append(LOCALHOST_ROUTE)
    secret = {"deviceID": "P", "apiKey": "decoy"}
    checks = {
        "old_route_detected": route_state(philip, lecun, [philip, lecun]) == "philip_only",
        "duplicate_route_rejected": route_state(philip, duplicate, [philip, duplicate]) == "duplicate",
        "missing_route_rejected": route_state({**philip, "addresses": []}, lecun, [{**philip, "addresses": []}, lecun]) == "missing",
        "secret_field_positive_control": contains_secret_field(secret),
        "ordinary_device_has_no_secret_field": not contains_secret_field(philip),
    }
    return checks, all(checks.values())


def main() -> int:
    parser = argparse.ArgumentParser()
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument("--inspect", action="store_true")
    actions.add_argument("--backup", type=Path)
    actions.add_argument("--set-lecun", action="store_true")
    actions.add_argument("--restore", type=Path)
    actions.add_argument("--self-test", action="store_true")
    parser.add_argument("--backup-dir", type=Path)
    args = parser.parse_args()
    if args.inspect:
        result = inspect()
        exit_code = 0
    elif args.backup:
        result = backup(args.backup)
        exit_code = 0
    elif args.set_lecun:
        if args.backup_dir is None:
            parser.error("--set-lecun requires --backup-dir")
        result = move_to_lecun(args.backup_dir)
        exit_code = 0
    elif args.restore:
        result = restore(args.restore)
        exit_code = 0
    else:
        checks, passed = self_test()
        result = {"self_test": checks, "result": "PASS" if passed else "FAIL"}
        exit_code = 0 if passed else 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
