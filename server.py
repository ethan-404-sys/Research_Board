import argparse
import json
import os
import re
import subprocess
import webbrowser
from datetime import datetime
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Lock

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data.json"
ENTRY_PATH = re.compile(r"^/api/entries/([A-Za-z0-9_-]+)$")
lock = Lock()


def git(*args):
    env = os.environ.copy()
    env["GIT_SSH_COMMAND"] = "ssh -o BatchMode=yes -o ConnectTimeout=10"
    return subprocess.run(
        ["git", *args], cwd=ROOT, env=env, capture_output=True,
        text=True, check=True, timeout=60,
    ).stdout.strip()


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

    def do_POST(self):
        if self.path != "/api/sync":
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        origin = self.headers.get("Origin")
        if origin and origin != f"http://{self.headers.get('Host')}":
            self.send_json({"error": "请求来源不匹配"}, HTTPStatus.FORBIDDEN)
            return
        if self.headers.get("Content-Type") != "application/json":
            self.send_json({"error": "需要 JSON 请求"}, HTTPStatus.BAD_REQUEST)
            return
        try:
            payload = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            entries = payload["entries"]
            if not isinstance(entries, list) or any(
                not isinstance(e, dict) or not isinstance(e.get("id"), str)
                or not re.fullmatch(r"[A-Za-z0-9_-]+", e["id"])
                or not e.get("date") or not isinstance(e.get("experiments"), list)
                for e in entries
            ):
                raise ValueError("卡片数据不完整")
        except (ValueError, KeyError, TypeError) as err:
            self.send_json({"error": f"无法保存：{err}"}, HTTPStatus.BAD_REQUEST)
            return
        try:
            with lock:
                board = load()
                updates = {e["id"]: e for e in entries}
                board["entries"] = [updates.pop(e["id"], e) for e in board["entries"]]
                board["entries"].extend(updates.values())
                if entries:
                    dump(board)
                if git("diff", "HEAD", "--", "data.json"):
                    git("commit", "--only", "-m", f"Update research progress {datetime.now():%Y-%m-%d %H:%M}", "--", "data.json")
                # 即使没有新改动，也重试上次尚未推送的提交。
                git("push", "origin", "HEAD:main")
        except subprocess.CalledProcessError as err:
            self.send_json({"error": "内容已保存在本机，同步失败：" + (err.stderr or err.stdout).strip()}, HTTPStatus.BAD_GATEWAY)
            return
        except subprocess.TimeoutExpired:
            self.send_json({"error": "内容已保存在本机，同步超时，请检查网络后重试。"}, HTTPStatus.GATEWAY_TIMEOUT)
            return
        self.send_json({"message": "已同步到 GitHub"})

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
