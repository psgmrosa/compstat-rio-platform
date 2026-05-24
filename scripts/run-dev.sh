#!/usr/bin/env bash
# Sobe backend FastAPI + frontend Next.js em paralelo, para desenvolvimento.
# Mata os dois processos quando você der Ctrl-C.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ ! -d .venv ]]; then
  echo "Criando venv e instalando dependências Python..."
  python3 -m venv .venv
  .venv/bin/pip install --quiet -e .
fi

if [[ ! -d web/node_modules ]]; then
  echo "Instalando dependências Node..."
  (cd web && npm install --no-audit --no-fund)
fi

cleanup() {
  echo
  echo "Parando processos..."
  kill 0 2>/dev/null || true
}
trap cleanup EXIT INT TERM

echo "→ FastAPI em http://localhost:8000  (docs em /docs)"
.venv/bin/uvicorn backend.main:app --reload --port 8000 &

echo "→ Next.js em http://localhost:3000"
(cd web && npm run dev) &

wait
