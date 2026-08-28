#!/usr/bin/env bash
# deploy-clean.sh — Reset limpo do projeto crmDeskIA na VPS.
# SEMPRE roda com -p crmdeskia para não afetar outros projetos.
set -euo pipefail
cd "$(dirname "$0")/.."

PROJECT="crmdeskia"

echo "=== Deploy limpo: $PROJECT ==="
echo "Parando containers e removendo volumes..."
docker compose -p "$PROJECT" down -v

echo "Rebuildando imagens sem cache..."
docker compose -p "$PROJECT" build --no-cache

echo "Subindo serviços..."
docker compose -p "$PROJECT" up -d

echo "=== Deploy concluído ==="
docker compose -p "$PROJECT" ps
