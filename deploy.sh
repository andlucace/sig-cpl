#!/bin/sh
# Roda NA VPS (dentro de /opt/sigcpl) para reimplantar depois de um `git push`
# feito de qualquer outro lugar. Local de trabalho: precisa ter .env.prod
# já presente (não versionado, ver .gitignore) e o remote 'origin' já
# configurado com a deploy key de leitura (ver README.md).
set -eu

cd "$(dirname "$0")"

git pull origin master

set -a
. ./.env.prod
set +a

docker compose -f docker-compose.prod.yml up -d --build
