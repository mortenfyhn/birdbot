#!/usr/bin/env bash
set -euo pipefail

birds=$("./birds.py")
[ -z "${birds}" ] && exit 0

curl -s "https://api.telegram.org/bot${TOKEN}/sendMessage" \
  --data "chat_id=${CHAT_ID}" \
  --data-urlencode "text=${birds}" \
  --data "disable_web_page_preview=true" >/dev/null
