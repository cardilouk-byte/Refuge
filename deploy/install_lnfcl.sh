#!/usr/bin/env bash
# ============================================================
#  LNFCL SIGES — Installasyon pwodiksyon sou Ubuntu 22/24 VPS
#  Itilizasyon:  sudo bash install_lnfcl.sh
#  Repons kesyon yo, script la fe tout rès la.
# ============================================================
set -euo pipefail

if [ "$EUID" -ne 0 ]; then echo "Dwe kòmanse ak sudo: sudo bash $0"; exit 1; fi

APP_DIR=${APP_DIR:-/opt/lnfcl}
REPO_URL=${REPO_URL:-https://github.com/cardilouk-byte/Refuge.git}
BRANCH=${BRANCH:-vibe/lnfcl-site-fc50d6}
SERVICE=lnfcl

echo "=========================================================="
echo " LNFCL SIGES — enstalasyon pwodiksyon"
echo " Repozitwa: $REPO_URL  (branch: $BRANCH)"
echo " Dosye app: $APP_DIR"
echo "=========================================================="
read -rp "Domèn ou (ex: lnfcl.eu.org) [si ou pa genyen, kite vid]: " DOMAIN
read -rp "Adrès imèl pou sètifikat / rapò [admin@lnfcl.edu]: " EMAIL
read -rsp "Mòdpas baz done PostgreSQL nouvo: " DB_PASSWORD; echo

echo "[1/9] Pakè sistèm..."
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq python3 python3-venv python3-pip git nginx postgresql postgresql-contrib curl

PYVER=$(python3 -c 'import sys; print("{}.{}".format(*sys.version_info[:2]))')
echo "    Python $PYVER detekte"
python3 - <<EOF || { echo "!! Django 6 bezwen Python 3.12+ — sèvi ak Ubuntu 24.04"; exit 1; }
import sys; assert sys.version_info >= (3, 12)
EOF

echo "[2/9] Kreye itilizatè sèvis lnfcl..."
id -u lnfcl &>/dev/null || useradd -r -m -d /home/lnfcl -s /usr/sbin/nologin lnfcl

echo "[3/9] Baz done PostgreSQL..."
sudo -u postgres psql -tc "SELECT 1 FROM pg_roles WHERE rolname='lnfcl'" | grep -q 1 || \
  sudo -u postgres psql -c "CREATE USER lnfcl WITH PASSWORD '$DB_PASSWORD';"
sudo -u postgres psql -tc "SELECT 1 FROM pg_database WHERE datname='lnfcl'" | grep -q 1 || \
  sudo -u postgres psql -c "CREATE DATABASE lnfcl OWNER lnfcl;"

echo "[4/9] Klonaj kòd la..."
if [ -d "$APP_DIR/.git" ]; then
  git -C "$APP_DIR" fetch --all -q
  git -C "$APP_DIR" checkout "$BRANCH" -q
  git -C "$APP_DIR" reset --hard "origin/$BRANCH" -q
else
  git clone -b "$BRANCH" "$REPO_URL" "$APP_DIR"
fi
cd "$APP_DIR"

echo "[5/9] Enviwònman Python (venv) + pakè..."
python3 -m venv venv
./venv/bin/pip install --quiet --upgrade pip
./venv/bin/pip install --quiet -r requirements.txt gunicorn psycopg[binary]

echo "[6/9] Fichye .env..."
SECRET_KEY="$(head -c 48 /dev/urandom | base64 | tr -d '=+/' | head -c 50)"
if [ -f .env ]; then
  echo "    .env deja egziste — nou pa manyen l."
else
  HOSTS="$DOMAIN"
  [ -z "$HOSTS" ] && HOSTS="$(curl -s -4 ifconfig.me || echo _)"
  cat > .env <<EOF
DEBUG=False
SECRET_KEY=$SECRET_KEY
ALLOWED_HOSTS=$HOSTS
DB_ENGINE=postgres
DB_NAME=lnfcl
DB_USER=lnfcl
DB_PASSWORD=$DB_PASSWORD
DB_HOST=localhost
DB_PORT=5432
ADMIN_URL=kontwol/
SECURE_SSL_REDIRECT=false   # mete true apre HTTPS la fini (gesyon sètificate)
EOF
  chmod 600 .env
fi

echo "[7/9] Migrasyon + fichye statik..."
chown -R lnfcl:www-data "$APP_DIR"
sudo -u lnfcl -E env DJANGO_SETTINGS_MODULE=config.settings \
  "$APP_DIR/venv/bin/python" "$APP_DIR/manage.py" migrate --noinput
sudo -u lnfcl -E env DJANGO_SETTINGS_MODULE=config.settings \
  "$APP_DIR/venv/bin/python" "$APP_DIR/manage.py" collectstatic --noinput 3>/dev/null

echo "[8/9] Sèvis Gunicorn (systemd)..."
cat > "/etc/systemd/system/$SERVICE.service" <<EOF
[Unit]
Description=LNFCL SIGES (Gunicorn)
After=network.target postgresql.service

[Service]
User=lnfcl
Group=www-data
WorkingDirectory=$APP_DIR
EnvironmentFile=$APP_DIR/.env
ExecStart=$APP_DIR/venv/bin/gunicorn config.wsgi:application --bind unix:/run/lnfcl.sock --workers 3 --timeout 120
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload
systemctl enable --now "$SERVICE"

echo "[9/9] Nginx + fwouwal..."
HOST_LINE="${DOMAIN:-_}"
cat > /etc/nginx/sites-available/lnfcl <<EOF
server {
    listen 80;
    server_name $HOST_LINE;

    client_max_body_size 160M;

    location /static/ { alias $APP_DIR/staticfiles/; expires 30d; access_log off; }
    location /media/  { alias $APP_DIR/media/;      expires 7d;  access_log off; }

    location / {
        include proxy_params;
        proxy_pass http://unix:/run/lnfcl.sock;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF
ln -sf /etc/nginx/sites-available/lnfcl /etc/nginx/sites-enabled/lnfcl
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx
ufw allow 'Nginx Full' 2>/dev/null || true
ufw allow OpenSSH 2>/dev/null || true

echo ""
echo "=========================================================="
echo " FE PA DRÈT SA YO KOUNYE A:"
echo "=========================================================="
echo " 1) Kreye kont admin (SIPÈADMIN):"
echo "    cd $APP_DIR && sudo -u lnfcl -E ./venv/bin/python manage.py createsuperuser"
echo " 2) Si ou gen done (db.sqlite3 / media/) soti sou Windows:"
echo "    scp -r medya user@seyvè:/$APP_DIR/media/ ; epi enpòte done yo"
echo " 3) Eta sèvis:  systemctl status $SERVICE"
echo " 4) Nan navigatè:  http://${DOMAIN:-IP_SÈVÈ}/"
echo "=========================================================="
