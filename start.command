#!/bin/zsh
DIR="$(cd "$(dirname "$0")" && pwd)"
PORT=47321
URL="http://127.0.0.1:$PORT/"

PID=$(lsof -nP -tiTCP:$PORT -sTCP:LISTEN)
if [[ -n "$PID" ]]; then
  CWD=$(lsof -a -p $PID -d cwd -Fn | sed -n 's/^n//p')
  if [[ "$CWD" == "$DIR" ]]; then
    echo "看板已经在运行，直接打开 $URL"
    open "$URL"
    exit 0
  fi
  echo "端口 $PORT 被其他程序占用（进程 $PID，工作目录 $CWD），看板无法启动。"
  exit 1
fi

cd "$DIR"
exec python3 server.py --port $PORT
