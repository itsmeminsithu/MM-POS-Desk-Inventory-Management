#!/bin/bash
cd "$(dirname "$0")" || exit 1
python3 start.py
status=$?
if [ "$status" -ne 0 ]; then
  read -r -p "Press Enter to close…"
fi
exit "$status"
