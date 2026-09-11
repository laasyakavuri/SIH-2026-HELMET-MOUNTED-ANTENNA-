#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
rm -f sih-smart-helmet-complete.zip ground-station.zip firmware.zip
find . -name node_modules -type d -prune -exec rm -rf {} + 2>/dev/null || true
zip -rq sih-smart-helmet-complete.zip . -x "*.zip" -x "*/.git/*" -x "bootstrap_sih.py"
zip -rq ground-station.zip ground-station
zip -rq firmware.zip firmware
echo "Created:"
unzip -l sih-smart-helmet-complete.zip | tail -1
unzip -l ground-station.zip | tail -1
unzip -l firmware.zip | tail -1
