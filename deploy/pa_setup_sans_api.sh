#!/usr/bin/env bash
# ================================================================
#  LNFCL SIGES — Setup PythonAnywhere SANS API (100% gratis)
#  Pa gen token, pa gen konfigirasyon API — tout bagay manwèl simplifie:
#  1) Kole kòmand sa a nan yon Bash console:
#       bash ~/Refuge/deploy/pa_setup_sans_api.sh
#     (si ~/Refuge poko egziste, script la klonel pou ou)
#  2) Ou pa bezwen Token — kesyon yo simpe, pou w peze Entrée.
#  Apre script la fini, ou gen 5 klike fè nan tab Web la (instruksyon
#  klè ap parèt nan fen script la, epi pwogram nan pwepare wsgi pou ou).
# ================================================================
set -euo pipefail

echo "==============================================="
echo " LNFCL SIGES — setup PythonAnywhere SANS API"
echo "==============================================="
echo ""

# ---- Klonaj si sa nesesè ----
APP="$HOME/Refuge"
BR="vibe/lnfcl-site-fc50d6"
REPO="https://github.com/cardilouk-byte/Refuge.git"

if [ ! -d "$APP" ]; then
  echo "==> Klonaj kòd la (yon fwa sèlman, ~30 sec)..."
  git clone -b "$BR" "$REPO" "$APP"
fi
git -C "$APP" fetch --all -q 2>/dev/null || true
git -C "$APP" checkout "$BR" -q 2>/dev/null || true
git -C "$APP" reset --hard "origin/$BR" -q 2>/dev/null || true
echo "   Kòd la an ($APP, branch $BR)"

# ---- venv ----
VENV="$HOME/.virtualenvs/lnfcl-env"
if [ ! -d "$VENV" ]; then
  echo ""
  echo "==> Kreye anviwònman Python 3.12 (yon fwa sèlman)..."
  mkvirtualenv lnfcl-env --python=python3.12 >/dev/null 2>&1 || \
    python3.12 -m venv "$VENV"
fi
source "$VENV/bin/activate"
echo "   Python: $(python --version)"

# ---- pakè ----
echo ""
echo "==> Enstale pakè yo (Django elatriye, ~2 min premye fwa)..."
pip install --quiet --upgrade pip
pip install --quiet -r "$APP/requirements.txt"
echo "   Pakè enstale."

# ---- .env ----
cd "$APP"
PU="$(whoami)"
PU_LOW="${PU,,}"          # PythonAnywhere domèn se tout miniskil
DOMAIN="${PU_LOW}.pythonanywhere.com"
if [ -f .env ]; then
  echo "==> .env deja egziste — n ap kenbe l."
else
  SECRET=$(python -c "import secrets; print(secrets.token_urlsafe(48))")
  cat > .env <<EOF
DEBUG=False
SECRET_KEY=$SECRET
ALLOWED_HOSTS=$DOMAIN
CSRF_TRUSTED_ORIGINS=https://$DOMAIN
ADMIN_URL=kontwol/
EOF
  echo "==> .env kreye (sekirize) — sit pou $DOMAIN"
fi

# ---- DB + statik ----
echo ""
echo "==> Migrate baz done a..."
python manage.py migrate --noinput

echo ""
echo "==> Fichye statik yo..."
python manage.py collectstatic --noinput 2>/dev/null | tail -1

echo ""
echo "==> Nete epi prepare wsgi (pou kopi colle pita)..."
cat > "$APP/deploy/wsgi_pa.txt" <<'WSEOF'
# LNFCL SIGES — kole tout sa ki anba a nan wsgi.py la (ranplase tout)
import os, sys
path = "{APP}"
if path not in sys.path:
    sys.path.insert(0, path)
os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings"
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
WSEOF
sed -i "s/{APP}/$APP/g" "$APP/deploy/wsgi_pa.txt"
# ---- superuser (opsyonèl) ----
echo ""
read -rp "--- Ou vle kreye kont SUPERADMIN kounye a? [o/N]: " REP
REPL=$(echo "${REP:-n}" | tr '[:upper:]' '[:lower:]')
if [ "$REPL" = "o" ] || [ "$REPL" = "oui" ] || [ "$REPL" = "y" ]; then
  python manage.py createsuperuser
fi

echo ""
echo "==============================================="
echo "  ✅ PARTI BASH LA FINI! Kounye a 5 KLIKE fè:"
echo "==============================================="
echo ""
echo " 1. Tab \"Web\" (anwo) → suns novèl web app:"
echo "      Add a new web app → Next"
echo "      → Manual configuration → Next"
echo "      → Python 3.10 oswa ki vèsyon pi wo n ap wè la → Next"
echo ""
echo " 2. Nan seksyon \"Code\" sou paj Web la:"
echo "      Source code:        $APP"
echo "      Working directory:  $APP"
echo "      Virtualenv:         $VENV"
echo "    (klike sou chak liy wòj, mete valè a, Save)"
echo ""
echo " 3. Klike sur text \"wsgi.py\" (toupre \"Source code\")"
echo "    EFFACE TOUT sa ki la — kole sa a sèlman:"
echo ""
echo "  ---------------------------- copie SOTI LA: ----------------------------"
sed 's/^/    /' "$APP/deploy/wsgi_pa.txt"
echo "  ----------------------------------------------------------------------"\necho ""
echo "    → Save (bouton anwo pou jwenn manje)"
echo ""
echo " 4. Nan seksyon \"Static files\" — ajoute 2 liy:"
echo "      URL: /static/      → Directory: $APP/staticfiles"
echo "      URL: /media/       → Directory: $APP/media"
echo ""
echo " 5. Woulo vèt anwo paj la: **Reload** (klike sou l)"
echo ""
echo "==============================================="
echo "  🌐 SIT OU AN:  https://$DOMAIN"
echo "  🔐 ADMIN:      https://$DOMAIN/kontwol/"
echo "==============================================="
echo ""
echo " REMAK:"
echo " - Si ou poko gen kont superadmin, nan Bash console a:"
echo "     workon lnfcl-env && cd ~/Refuge && python manage.py createsuperuser"
echo " - Si sit la pa kòrèk, gade tab Web → Error log (50x)"
echo " - Re-fè script la nenpòt lè pou update: li rale dènye kòd la"
echo "==============================================="
