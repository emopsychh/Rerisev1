#!/bin/sh
set -e

DOMAIN="${DOMAIN:-localhost}"
LE_DIR="/etc/letsencrypt/live/${DOMAIN}"
SSL_DIR="/etc/nginx/ssl"

mkdir -p "$SSL_DIR" /var/www/certbot

if [ -f "${LE_DIR}/fullchain.pem" ] && [ -f "${LE_DIR}/privkey.pem" ]; then
  echo "Using Let's Encrypt certificate for ${DOMAIN}"
  ln -sf "${LE_DIR}/fullchain.pem" "${SSL_DIR}/fullchain.pem"
  ln -sf "${LE_DIR}/privkey.pem" "${SSL_DIR}/privkey.pem"
else
  echo "No LE cert yet — temporary self-signed for ${DOMAIN}"
  openssl req -x509 -nodes -newkey rsa:2048 -days 1 \
    -keyout "${SSL_DIR}/privkey.pem" \
    -out "${SSL_DIR}/fullchain.pem" \
    -subj "/CN=${DOMAIN}"
fi

exec /docker-entrypoint.sh "$@"
