#!/usr/bin/env bash
# ================================================================
#  LNFCL SIGES — Setup OTOMATIK PythonAnywhere (100% gratis)
#  KOTE POU L KOURI: nan yon Bash console PythonAnywhere →
#      cd ~ && git clone -b vibe/lnfcl-site-fc50d6 https://github.com/cardilouk-byte/Refuge.git 2>/dev/null; bash ~/Refuge/deploy/pa_setup.sh
#  Script la mande w: username ou + API token (Web tab > API Token)
# ================================================================
set -euo pipefail

echo "=============================================="
echo " LNFCL SIGES — setup otomatik PythonAnywhere"
echo "=============================================="
read -rp "Username PythonAnywhere [Entrée = $(whoami)]: " IN_USER
PU="${IN_USER:-$(whoami)}"
read -rsp "API token ou (Web tab > API Token > Create): " PT; echo
echo ""

DOMAIN="$PU.pythonanywhere.com"
API="https://www.pythonanywhere.com/api/v0/user/$PU"
AUTH="Authorization: Token $PT"
APP="$HOME/Refuge"
VENV="$HOME/.virtualenvs/lnfcl-env"
BR="vibe/lnfcl-site-fc50d6"

step() { echo ""; echo "==> $1"; }

step "[1/9] Klonaj kòd la..."
if [ -d "$APP/.git" ]; then
  git -C "$APP" fetch --all -q
else
  git clone -b "$BR" https://github.com/cardilouk-byte/Refuge.git "$APP"
fi
git -C "$APP" checkout "$BR" -q || true
git -C "$APP" reset --hard "origin/$BR" -q

step "[2/9] Enviwònman Python (venv) 3.12..."
if [ ! -d "$VENV" ]; then
  mkvirtualenv lnfcl-env --python=python3.12 >/dev/null 2>&1 || \
    python3.12 -m venv "$VENV"
fi
# deactivate lòt venv, aktive nòt la
source "$VENV/bin/activate" 2>/dev/null || { echo "!! venv pa aktive"; exit 1; }

step "[3/9] Pakè Django + tout bagay..."
pip install --quiet --upgrade pip
pip install --quiet -r "$APP/requirements.txt"

step "[4/9] Fichye .env..."
cd "$APP"
if [ -f .env ]; then
  echo "    .env deja egziste — kenbe l."
else
  SECRET=$(python -c "import secrets; print(secrets.token_urlsafe(48))")
  cat > .env <<EOF
DEBUG=False
SECRET_KEY=$SECRET
ALLOWED_HOSTS=$DOMAIN
CSRF_TRUSTED_ORIGINS=https://$DOMAIN
ADMIN_URL=kontwol/
EOF
  echo "    .env kreye (SIPÈSEKIRITE)."
fi

step "[5/9] Baz done (migrate)..."
python "$APP/manage.py" migrate --noinput

step "[6/9] Fichye statik (collectstatic)..."
python "$APP/manage.py" collectstatic --noinput 2>/dev/null | tail -1

step "[7/9] Kreye web app la via API..."
HTTP=$(curl -s -o /tmp/pa_resp.json -w "%{http_code}" -X POST "$API/webapps/" \
  -H "$AUTH" -H "Content-Type: application/json" \
  -d "{\"domain\": \"$DOMAIN\", \"python_version\": \"3.12\"}" || echo 000)
if [ "$HTTP" = "201" ]; then
  echo "    Web app '$DOMAIN' kreye."
elif [ "$HTTP" = "400" ]; then
  echo "    Web app deja egziste — n ap konfigire l."
else
  echo "    API webapp create (HTTP $HTTP) — n ap kontinye tou."
  cat /tmp/pa_resp.json || true
fi

step "[8/9] Konfigirasyon (source, venv, wsgi, static)..."
curl -s -X PATCH "$API/webapps/$DOMAIN/" -H "$AUTH" -H "Content-Type: application/json" \
  -d "{\"source_directory\": \"$APP\", \"python_version\": \"3.12\"}" >/dev/null
curl -s -X PATCH "$API/webapps/$DOMAIN/" -H "$AUTH" -H "Content-Type: application/json" \
  -d "{\"virtualenv_path\": \"$VENV\"}" >/dev/null
curl -s -X PATCH "$API/webapps/$DOMAIN/" -H "$AUTH" -H "Content-Type: application/json" \
  -d "{\"static_files\": {\"/static/\": \"$APP/staticfiles\", \"/media/\": \"$APP/media\"}}" >/dev/null
  
WSGI="/var/www/${PU}_pythonanywhere_com_wsgi.py"
if [ -f "$WSGI" ]; then
  cat > "$WSGI" <<EOF
import os, sys
path = "$APP"
if path not in sys.path:
    sys.path.insert(0, path)
os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings"
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
EOF
  echo "    wsgi.py ekri."
fi

step "[9/9] Reload sit lan..."
curl -s -X POST "$API/webapps/$DOMAIN/reload/" -H "$AUTH" >/dev/null

echo ""
echo "=============================================="
echo "  ✅ FINI! Sit ou an:  https://$DOMAIN"
echo "=============================================="
echo " RETE POU W (yon sèl bagay):"
echo "   Kreye kont SIPÈADMIN lan:"
echo "     workon lnfcl-env && cd ~/Refuge && python manage.py createsuperuser"
echo ""
echo "   Admin: https://$DOMAIN/kontwol/"
echo ""
echo "   Si yon bagay pa mache, Gade tab Web > Error log,"
echo "   oswa re-run setup sa a apre w fin repare l."
echo "=============================================="
