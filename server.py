#!/usr/bin/env python3
"""OPTCG 組牌造價網站 — 本機伺服器。"""
from __future__ import annotations

import argparse
import json
import mimetypes
import os
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from kapaipai import price_deck

ROOT = Path(__file__).resolve().parent
STATIC = ROOT / "static"
DEFAULT_PORT = int(os.environ.get("PORT", "8765"))
DEFAULT_HOST = os.environ.get("HOST", "127.0.0.1")


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args) -> None:
        print(f"[{self.log_date_time_string()}] {fmt % args}")

    def _send_json(self, data: dict, status: int = 200) -> None:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, path: Path) -> None:
        if not path.is_file():
            self.send_error(404)
            return
        content = path.read_bytes()
        mime, _ = mimetypes.guess_type(str(path))
        self.send_response(200)
        self.send_header("Content-Type", mime or "application/octet-stream")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path in ("/", "/index.html"):
            self._send_file(STATIC / "index.html")
            return
        if parsed.path.startswith("/static/"):
            rel = parsed.path.removeprefix("/static/")
            target = (STATIC / rel).resolve()
            if not str(target).startswith(str(STATIC.resolve())):
                self.send_error(403)
                return
            self._send_file(target)
            return
        self.send_error(404)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path != "/api/price-deck":
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length else b"{}"
        try:
            payload = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            self._send_json({"error": "無效的 JSON"}, status=400)
            return
        deck = str(payload.get("deck", "")).strip()
        mode = payload.get("mode", "standard")
        if mode not in ("standard", "cheapest"):
            mode = "standard"
        basis = payload.get("basis", "average")
        if basis not in ("average", "lowest"):
            basis = "average"
        if not deck:
            self._send_json({"error": "請貼上牌組內容"}, status=400)
            return
        try:
            result = price_deck(deck, mode=mode, basis=basis)
            self._send_json(result)
        except Exception as exc:
            self._send_json({"error": f"查價失敗：{exc}"}, status=500)


def open_browser(host: str, port: int) -> None:
    url = f"http://{host}:{port}/"
    threading.Timer(0.6, lambda: webbrowser.open(url)).start()


def main() -> None:
    parser = argparse.ArgumentParser(description="OPTCG 組牌造價網站")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--open", action="store_true", help="啟動後自動開啟瀏覽器")
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    url = f"http://{args.host}:{args.port}"
    print(f"OPTCG 組牌造價：{url}")
    print("按 Ctrl+C 結束")
    if args.open:
        open_browser(args.host, args.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止")
        server.server_close()


if __name__ == "__main__":
    main()
