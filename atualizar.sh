#!/bin/bash
# Atualiza a apresentação: tira as fotos do banco (requer VPN) e regera index.html + PDF.
# Uso: ./atualizar.sh
set -euo pipefail
cd "$(dirname "$0")"

DEPS=(--with pandas --with openpyxl --with python-dotenv --with msoffcrypto-tool)

echo "== 1/2 extração do banco"
uv run --quiet "${DEPS[@]}" --with sqlalchemy --with psycopg2-binary python python/extrair.py

echo "== 2/2 build"
uv run --quiet "${DEPS[@]}" python build.py

echo
echo "Pronto. Se os dados mudaram: suba a VERSAO, acrescente a linha em HISTORICO no build.py,"
echo "rode o build de novo e faça o commit (data/, index.html e o PDF)."
