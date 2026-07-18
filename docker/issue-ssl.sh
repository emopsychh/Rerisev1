#!/bin/sh
# Issue Let's Encrypt certificate. Run from repo root after DNS points here.
#   chmod +x docker/issue-ssl.sh && ./docker/issue-ssl.sh
set -e

cd "$(dirname "$0")/.."

if [ ! -f .env ]; then
  echo "Missing .env in repo root"
  exit 1
fi

# Do NOT `source` .env — secrets often contain $, (), & that break the shell.
env_get() {
  # KEY=value → value (first = only); strip CR and surrounding quotes
  grep -E "^${1}=" .env | head -n1 | cut -d= -f2- | tr -d '\r' | sed -e 's/^"//' -e 's/"$//' -e "s/^'//" -e "s/'$//"
}

DOMAIN="$(env_get DOMAIN)"
SSL_EMAIL="$(env_get SSL_EMAIL)"

DOMAIN="${DOMAIN:-systema.site}"
EMAIL="${SSL_EMAIL:-admin@${DOMAIN}}"

echo "Requesting certificate for ${DOMAIN} (email: ${EMAIL})..."

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
