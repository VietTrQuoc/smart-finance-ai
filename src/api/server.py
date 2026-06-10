"""Serve the static dashboard and local JSON API."""

from __future__ import annotations

import argparse
import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

from src.backend.dashboard_data import load_dashboard_payload


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DASHBOARD_ROOT = PROJECT_ROOT / "dashboard"


class DashboardRequestHandler(BaseHTTPRequestHandler):
    server_version = "SmartFinanceDashboard/0.1"

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/health":
            self.write_json({"status": "ok"})
            return
        if path == "/api/dashboard":
            self.write_json(load_dashboard_payload(PROJECT_ROOT).to_api())
            return
        if path == "/api/leads":
            self.write_json({"leads": load_dashboard_payload(PROJECT_ROOT).leads})
            return
        if path == "/api/fraud/alerts":
            self.write_json({"fraudAlerts": load_dashboard_payload(PROJECT_ROOT).fraud_alerts})
            return
        if path.startswith("/api/users/") and path.endswith("/recommendations"):
            user_id = unquote(path.removeprefix("/api/users/").removesuffix("/recommendations"))
            lead = next(
                (
                    item
                    for item in load_dashboard_payload(PROJECT_ROOT).leads
                    if item["id"] == user_id
                ),
                None,
            )
            if lead is None:
                self.write_json({"error": "user_not_found"}, HTTPStatus.NOT_FOUND)
            else:
                self.write_json(lead)
            return

        self.serve_static(path)

    def serve_static(self, path: str) -> None:
        if path in {"/", ""}:
            target = DASHBOARD_ROOT / "index.html"
        else:
            requested = unquote(path.lstrip("/"))
            if requested.startswith("dashboard/"):
                requested = requested.removeprefix("dashboard/")
            target = DASHBOARD_ROOT / requested

        try:
            resolved = target.resolve()
            resolved.relative_to(DASHBOARD_ROOT.resolve())
        except ValueError:
            self.write_json({"error": "invalid_path"}, HTTPStatus.BAD_REQUEST)
            return

        if not resolved.exists() or not resolved.is_file():
            self.write_json({"error": "not_found"}, HTTPStatus.NOT_FOUND)
            return

        content_type = content_type_for(resolved)
        body = resolved.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def write_json(self, payload: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args) -> None:
        return


def content_type_for(path: Path) -> str:
    if path.suffix == ".html":
        return "text/html; charset=utf-8"
    if path.suffix == ".css":
        return "text/css; charset=utf-8"
    if path.suffix == ".js":
        return "application/javascript; charset=utf-8"
    return "application/octet-stream"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Serve Smart Finance AI dashboard")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    server = ThreadingHTTPServer((args.host, args.port), DashboardRequestHandler)
    print(f"Serving dashboard at http://{args.host}:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
