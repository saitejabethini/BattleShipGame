#!/usr/bin/env bash
# Render the three.js scene to PNG with headless Chrome. Usage: render3d.sh ne se sw ...
set -e
cd "$(dirname "$0")/three"
OUT="../../v2"
python3 -m http.server 8765 >/dev/null 2>&1 &
SRV=$!
trap "kill $SRV 2>/dev/null" EXIT
sleep 1
for v in "$@"; do
  timeout 45 /usr/local/bin/google-chrome --headless=new --no-sandbox --disable-gpu-sandbox --use-angle=swiftshader --enable-unsafe-swiftshader --ignore-gpu-blocklist \
    --window-size=1600,1000 --hide-scrollbars --virtual-time-budget=20000 \
    --screenshot="$OUT/view3d-$v.png" "http://localhost:8765/scene.html?view=$v" >/dev/null 2>&1 || true
  echo "rendered $v"
done
