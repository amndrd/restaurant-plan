#!/bin/zsh
# Opens the interactive map: serves this folder on a free local port and opens it in the browser.
# Closing this window stops the server.
cd "$(dirname "$0")"
PORT=8765
while lsof -i :$PORT >/dev/null 2>&1; do PORT=$((PORT + 1)); done
python3 -m http.server $PORT --bind 127.0.0.1 >/dev/null 2>&1 &
sleep 0.6
open "http://127.0.0.1:$PORT/"
echo "La carte est ouverte sur http://127.0.0.1:$PORT/ (fermer cette fenêtre arrête le serveur)."
wait
