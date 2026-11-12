#!/usr/bin/env bash
#
# Menjalankan aplikasi di lokal memakai container (Podman/Docker) dengan PHP 8.2.
#
# Pemakaian:
#   bash scripts/serve-local.sh          # http://localhost:8000
#   PORT=8080 bash scripts/serve-local.sh
#
# Container dipakai karena repo ini memakai Laravel 10 yang tidak kompatibel
# dengan PHP 8.5 (satu-satunya versi PHP di repo Fedora 45).
#
set -euo pipefail
cd "$(dirname "$0")/.."

PORT="${PORT:-8000}"
PHP_IMAGE="docker.io/library/php:8.2-cli-alpine"
COMPOSER_IMAGE="docker.io/library/composer:2"

if command -v podman >/dev/null 2>&1; then
    ENGINE="podman"
elif command -v docker >/dev/null 2>&1; then
    ENGINE="docker"
else
    echo "Error: Podman atau Docker tidak ditemukan." >&2
    exit 1
fi

# :Z diperlukan untuk SELinux (Fedora). Docker Desktop tidak memakainya.
MOUNT_SUFFIX=""
if [ "$(getenforce 2>/dev/null || true)" = "Enforcing" ]; then
    MOUNT_SUFFIX=":Z"
fi

run_php() {
    "$ENGINE" run --rm -e HOME=/tmp -v "$PWD":/app$MOUNT_SUFFIX -w /app "$PHP_IMAGE" php "$@"
}

if [ ! -d vendor ]; then
    echo "==> Dependency belum ada, menjalankan composer install..."
    "$ENGINE" run --rm -e HOME=/tmp -e COMPOSER_HOME=/tmp/composer \
        -v "$PWD":/app$MOUNT_SUFFIX -w /app "$COMPOSER_IMAGE" \
        install --no-interaction --no-scripts --prefer-dist --ignore-platform-req=php
    run_php artisan package:discover --ansi
fi

if [ ! -f .env ]; then
    echo "==> Membuat file .env..."
    cat > .env <<'EOF'
APP_NAME="MBJ Indonesia"
APP_ENV=local
APP_KEY=
APP_DEBUG=true
APP_URL=http://localhost:8000

LOG_CHANNEL=stack
LOG_DEPRECATIONS_CHANNEL=null
LOG_LEVEL=debug

DB_CONNECTION=sqlite

BROADCAST_DRIVER=log
CACHE_DRIVER=file
FILESYSTEM_DISK=local
QUEUE_CONNECTION=sync
SESSION_DRIVER=file
SESSION_LIFETIME=120

MAIL_MAILER=log
EOF
fi

if ! grep -q '^APP_KEY=base64:' .env; then
    run_php artisan key:generate --force
fi

if [ ! -f database/database.sqlite ]; then
    touch database/database.sqlite
    run_php artisan migrate --force
fi

echo
echo "==> Aplikasi berjalan di: http://localhost:$PORT"
echo "    Hentikan dengan Ctrl+C."
echo

"$ENGINE" rm -f mbj-local >/dev/null 2>&1 || true

exec "$ENGINE" run --rm --name mbj-local -p "$PORT":8000 \
    -e HOME=/tmp -v "$PWD":/app$MOUNT_SUFFIX -w /app "$PHP_IMAGE" \
    php artisan serve --host=0.0.0.0 --port=8000
