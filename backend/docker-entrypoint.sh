#!/bin/sh
set -eu

SQLITE_TARGET="${SQLITE_PATH:-/tmp/ludostock.db}"
SQLITE_SOURCE="${SQLITE_SEED_PATH:-}"

if [ -n "$SQLITE_SOURCE" ] && [ ! -f "$SQLITE_TARGET" ]; then
  if [ -f "$SQLITE_SOURCE" ]; then
    mkdir -p "$(dirname "$SQLITE_TARGET")"
    cp "$SQLITE_SOURCE" "$SQLITE_TARGET"
    echo "Seeded SQLite database from $SQLITE_SOURCE to $SQLITE_TARGET"
  else
    echo "SQLite seed file not found at $SQLITE_SOURCE, starting with $SQLITE_TARGET"
  fi
fi

exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8081}"
