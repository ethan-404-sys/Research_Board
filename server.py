import argparse
import json
import os
import re
import webbrowser
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Lock

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data.json"
ENTRY_PATH = re.compile(r"^/api/entries/([A-Za-z0-9_-]+)$")
lock = Lock()


def load():
    return json.loads(DATA.read_text(encoding="utf-8"))


def dump(board):
    # 先写临时文件再替换，避免写到一半时文件损坏
    tmp = DATA.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(board, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, DATA)


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def send_json(self, obj, status=HTTPStatus.OK):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/api/data":
            with lock:
                self.send_json(load())
            return
        super().do_GET()

    def do_PUT(self):
        m = ENTRY_PATH.match(self.path)
        if not m:
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        entry = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        if entry["id"] != m.group(1):
            self.send_error(HTTPStatus.BAD_REQUEST, "id 不一致")
            return
        with lock:
            board = load()
            entries = board["entries"]
            idx = next((i for i, e in enumerate(entries) if e["id"] == entry["id"]), None)
            if idx is None:
                entries.append(entry)
            else:
                entries[idx] = entry
            dump(board)
        self.send_json(entry)

    def do_DELETE(self):
        m = ENTRY_PATH.match(self.path)
        if not m:
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        with lock:
            board = load()
            before = len(board["entries"])
            board["entries"] = [e for e in board["entries"] if e["id"] != m.group(1)]
            if len(board["entries"]) == before:
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            dump(board)
        self.send_json({"deleted": m.group(1)})


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=47321)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    url = f"http://127.0.0.1:{args.port}/"
    print(f"科研进度看板：{url}  （Ctrl+C 停止）")
    if not args.no_browser:
        webbrowser.open(url)
    server.serve_forever()
