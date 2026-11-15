#!/usr/bin/env sh
cd "$(dirname "$0")" || exit 1
if command -v node >/dev/null 2>&1; then
  echo 'Mo http://localhost:8766 trong trinh duyet'
  exec node server.mjs
elif command -v python3 >/dev/null 2>&1; then
  echo 'Mo http://localhost:8766 trong trinh duyet'
  exec python3 -m http.server 8766 --bind 127.0.0.1
else
  echo 'Can Node.js hoac Python 3'
  exit 1
fi
