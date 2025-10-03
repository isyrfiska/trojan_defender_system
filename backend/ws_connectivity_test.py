#!/usr/bin/env python
import json
import time
import requests
import websocket
import os
import argparse

BASE_URL = "http://127.0.0.1:8000"
ADMIN_EMAIL = "admin@trojandefender.com"
ADMIN_PASSWORD = "TrojanDefender2024!"


# Parameterization defaults from environment
DEFAULT_BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8000")
DEFAULT_ADMIN_EMAIL = os.getenv("TD_ADMIN_EMAIL", "admin@trojandefender.com")
DEFAULT_ADMIN_PASSWORD = os.getenv("TD_ADMIN_PASSWORD", "TrojanDefender2024!")


def parse_args():
    parser = argparse.ArgumentParser(description="WebSocket connectivity test")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="Base HTTP URL, e.g. http://127.0.0.1:8000")
    parser.add_argument("--email", default=DEFAULT_ADMIN_EMAIL, help="Login email (can be provided via TD_ADMIN_EMAIL env)")
    parser.add_argument("--password", default=DEFAULT_ADMIN_PASSWORD, help="Login password (can be provided via TD_ADMIN_PASSWORD env)")
    parser.add_argument("--run-general", action="store_true", help="Run General WebSocket test")
    parser.add_argument("--run-ti", action="store_true", help="Run Threat Intelligence WebSocket test")
    parser.add_argument("--run-map", action="store_true", help="Run Threat Map WebSocket test")
    parser.add_argument("--filters-severity", default="high", help="Threat Map filter severity (e.g., high, medium)")
    parser.add_argument("--filters-days", type=int, default=30, help="Threat Map filter days window")
    parser.add_argument("--no-create-event", action="store_true", help="Skip creating a ThreatEvent during map test")
    return parser.parse_args()


def http_to_ws(url: str) -> str:
    if url.startswith("https://"):
        return "wss://" + url[len("https://"):]
    if url.startswith("http://"):
        return "ws://" + url[len("http://"):]
    return url


def get_access_token(base_url: str, email: str, password: str) -> str:
    url = f"{base_url}/api/auth/login/"
    resp = requests.post(url, json={"email": email, "password": password})
    print(f"Login status: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        token = data.get("access")
        print("Obtained access token.")
        return token
    raise RuntimeError(f"Login failed: {resp.text}")


def test_general_websocket(token: str, base_url: str) -> None:
    ws_url = f"{http_to_ws(base_url)}/ws/?token={token}"
    print(f"Connecting to general WS: {ws_url}")
    ws = websocket.create_connection(ws_url, timeout=10)
    print("Connected (general WS)")

    # Subscribe and ping
    ws.send(json.dumps({"type": "subscribe", "channel": "system_notifications"}))
    ws.send(json.dumps({"type": "ping", "timestamp": int(time.time())}))

    ws.settimeout(10)
    try:
        for _ in range(3):
            msg = ws.recv()
            print("[general] Received:", msg)
    except Exception as e:
        print("[general] No more messages or error:", e)
    finally:
        ws.close()
        print("Closed (general WS)")


def test_threat_intelligence_ws(token: str, base_url: str) -> None:
    ws_url = f"{http_to_ws(base_url)}/ws/threat-intelligence/?token={token}"
    print(f"Connecting to TI WS: {ws_url}")
    ws = websocket.create_connection(ws_url, timeout=10)
    print("Connected (TI WS)")

    # Request initial data
    ws.send(json.dumps({"type": "get_stats"}))
    ws.send(json.dumps({"type": "get_recent_threats", "limit": 5}))

    ws.settimeout(10)
    try:
        for _ in range(5):
            msg = ws.recv()
            print("[ti] Received:", msg)
    except Exception as e:
        print("[ti] No more messages or error:", e)
    finally:
        ws.close()
        print("Closed (TI WS)")


def create_threat_event(token: str, base_url: str) -> None:
    """Create a ThreatEvent via REST API to trigger WS broadcast."""
    url = f"{base_url}/api/threatmap/events/"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {
        "threat_type": "worm",
        "severity": "high",
        "ip_address": "8.8.4.4",
        "country": "United States",
        "city": "Atlanta",
        "latitude": 33.7490,
        "longitude": -84.3880,
        "description": "Realtime injected worm from WS test",
        "file_name": "ws_test_payload.exe",
        "file_hash": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
    }
    print("Creating ThreatEvent via API to trigger WS update...")
    resp = requests.post(url, headers=headers, json=payload, timeout=10)
    print(f"Create event status: {resp.status_code}")
    try:
        print("Create event response:", resp.json())
    except Exception:
        print("Create event response (raw):", resp.text)


def test_threat_map_ws(token: str, base_url: str, severity: str = "high", days: int = 30, create_event: bool = True) -> None:
    ws_url = f"{http_to_ws(base_url)}/ws/threat-map/?token={token}"
    print(f"Connecting to Threat Map WS: {ws_url}")
    ws = websocket.create_connection(ws_url, timeout=10)
    print("Connected (Threat Map WS)")

    # Subscribe to filters and request threat data (supported message types)
    ws.send(json.dumps({"type": "subscribe_filters", "filters": {"days": days, "severity": severity}}))
    ws.send(json.dumps({"type": "get_threats", "filters": {"days": days, "severity": severity}}))

    # Optionally create a new event via API to ensure delivery
    if create_event:
        create_threat_event(token, base_url)

    ws.settimeout(15)
    try:
        for _ in range(10):
            msg = ws.recv()
            print("[map] Received:", msg)
    except Exception as e:
        print("[map] No more messages or error:", e)
    finally:
        ws.close()
        print("Closed (Threat Map WS)")


if __name__ == "__main__":
    args = parse_args()
    base_url = args.base_url
    email = args.email
    password = args.password

    token = get_access_token(base_url, email, password)

    # If no specific run flag provided, run all
    run_all = not any([args.run_general, args.run_ti, args.run_map])

    if args.run_general or run_all:
        test_general_websocket(token, base_url)

    if args.run_ti or run_all:
        test_threat_intelligence_ws(token, base_url)

    if args.run_map or run_all:
        test_threat_map_ws(
            token,
            base_url,
            severity=args.filters_severity,
            days=args.filters_days,
            create_event=(not args.no_create_event)
        )