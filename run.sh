#!/usr/bin/env bash
cd "$(dirname "$0")"
PORT="${PORT:-5006}"
echo "=========================================================="
echo "  ShiftMaster - Jadwal Kerja Engineering Taman Anggrek Residence"
echo "  Server berjalan di: http://localhost:$PORT"
echo "=========================================================="
if [ -d ".venv" ]; then
  .venv/bin/python app.py
else
  python3 app.py
fi
