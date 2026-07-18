#!/bin/sh
# Issue Let's Encrypt certificate. Run from repo root after DNS points here.
#   chmod +x docker/issue-ssl.sh && ./docker/issue-ssl.sh
set -e

cd "$(dirname "$0")/.."

if [ ! -f .env ]; then
  echo "Missing .env in repo root"
  exit 1
fi

set -a
# shellcheck disable=SC1091
. ./.env
set +a

DOMAIN="${DOMAIN:-systema.site}"
EMAIL="${SSL_EMAIL:-admin@${DOMAIN}}"

echo "Requesting certificate for ${DOMAIN}..."

docker compose run --rm --entrypoint certbot certbot certonly \
  --webroot \
  --webroot-path=/var/www/certbot \
  --email "$EMAIL" \
  --agree-tos \
  --no-eff-email \
  -d "$DOMAIN"

echo "Recreating nginx to pick up certificate..."
docker compose up -d --force-recreate nginx

echo "Done → https://${DOMAIN}/"
