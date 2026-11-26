#!/usr/bin/env bash
# LNFCL SIGES — mete ajou vèsyon an (apre chak nouvo kòd pouse sou GitHub)
# Itilizasyon:  sudo bash update_lnfcl.sh [domain-akseswa-kòbjen-inen]
set -euo pipefail
APP_DIR=${APP_DIR:-/opt/lnfcl}
SERVICE=lnfcl
cd "$APP_DIR"

echo "[1/4] Kode noufè (git)..."
git fetch --all -q
CUR=$(git rev-parse --abbrev-ref HEAD)
git checkout "$CUR" -q
git reset --hard "origin/$CUR" -q
echo "    Ajour ak origin/$CUR ($(git rev-parse --short HEAD))"

echo "[2/4] Pakè Python..."
./venv/bin/pip install --quiet --upgrade pip
./venv/bin/pip install --quiet -r requirements.txt gunicorn

echo "[3/4] Migrasyon + statik..."
sudo -u lnfcl -E env DJANGO_SETTINGS_MODULE=config.settings \
  ./venv/bin/python manage.py migrate --noinput
sudo -u lnfcl -E env DJANGO_SETTINGS_MODULE=config.settings \
  ./venv/bin/python manage.py collectstatic --noinput 3>/dev/null
chown -R lnfcl:www-data "$APP_DIR"

echo "[4/4] Repris sèvis..."
systemctl restart "$SERVICE"
systemctl is-active --quiet "$SERVICE" && echo "OK — sit la ajou ✅"
