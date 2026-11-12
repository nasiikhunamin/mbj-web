#!/usr/bin/env bash
#
# Kompres foto galeri tanpa mengubah rasio/tampilan.
#
# Pemakaian:
#   bash scripts/optimize-galeri.sh              # proses foto baru saja
#   bash scripts/optimize-galeri.sh --force      # proses ulang semua foto
#
# Cara kerja:
#   - File asli disimpan sekali ke storage/app/galeri-original/ (tidak di public).
#   - Sisi terpanjang diperkecil ke maksimal 1400 px (masih tajam untuk web/retina).
#   - Kualitas JPEG 85, progressive, metadata dibuang.
#   - File hanya ditimpa jika hasilnya lebih kecil dari aslinya.
#
set -euo pipefail

DIR="public/asset/img"
BACKUP="storage/app/galeri-original"
MAX=1400
QUALITY=85
FORCE=0

for arg in "$@"; do
    case "$arg" in
        --force) FORCE=1 ;;
        --*) echo "Opsi tidak dikenal: $arg" >&2; exit 1 ;;
        *) DIR="$arg" ;;
    esac
done

if ! command -v magick >/dev/null 2>&1; then
    echo "Error: ImageMagick (perintah 'magick') tidak ditemukan." >&2
    exit 1
fi

mkdir -p "$BACKUP"
shopt -s nullglob nocaseglob

total=0
optimized=0
saved=0

for file in "$DIR"/galery-*.jpeg "$DIR"/galery-*.jpg; do
    [ -f "$file" ] || continue
    name=$(basename "$file")
    total=$((total + 1))

    if [ -f "$BACKUP/$name" ] && [ "$FORCE" -ne 1 ]; then
        echo "lewati   $name (sudah pernah diproses)"
        continue
    fi

    # Foto yang sudah kecil & resolusinya wajar tidak perlu dikompres ulang.
    if [ "$FORCE" -ne 1 ] && [ "$(stat -c%s "$file")" -le 262144 ] \
        && [ "$(magick identify -format '%[fx:max(w,h)]' "$file")" -le "$MAX" ]; then
        echo "lewati   $name (sudah ringan)"
        continue
    fi

    [ -f "$BACKUP/$name" ] || cp -p "$file" "$BACKUP/$name"

    tmp=$(mktemp --suffix=.jpg)
    magick "$file" \
        -auto-orient \
        -resize "${MAX}x${MAX}>" \
        -strip \
        -interlace Plane \
        -sampling-factor 4:2:0 \
        -quality "$QUALITY" "$tmp"

    before=$(stat -c%s "$file")
    after=$(stat -c%s "$tmp")

    if [ "$after" -lt "$before" ]; then
        mv "$tmp" "$file"
        optimized=$((optimized + 1))
        saved=$((saved + before - after))
        printf 'kompres  %-20s %6s KB -> %5s KB\n' "$name" \
            "$((before / 1024))" "$((after / 1024))"
    else
        rm -f "$tmp"
        echo "tetap    $name (hasil kompres tidak lebih kecil)"
    fi
done

echo
echo "Selesai: $optimized dari $total foto dikompres, hemat $((saved / 1024)) KB."
[ "$optimized" -gt 0 ] && echo "Backup file asli: $BACKUP/"
