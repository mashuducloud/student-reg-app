#!/usr/bin/env bash
# Normalize line endings of shell scripts (CRLF -> LF) and ensure executable.
# Usage: bash .github/scripts/fix-crlf.sh [globs/files...]
set -euo pipefail
shopt -s nullglob

if [ "$#" -eq 0 ]; then
  set -- .github/scripts/*.sh infra/*.sh scripts/*.sh
fi

normalized=0
for f in "$@"; do
  [ -f "$f" ] || continue
  sed -i 's/\r$//' "$f" || {
    awk '{ sub(/\r$/,""); print }' "$f" >"$f.tmp" && mv "$f.tmp" "$f"
  }
  tail -c1 "$f" | od -An -t x1 | grep -qi '0a' >/dev/null 2>&1 || printf '\n' >>"$f"
  chmod +x "$f" || true
  echo "normalized: $f"
  normalized=$((normalized+1))
done

echo "done: ${normalized} file(s) normalized)"
