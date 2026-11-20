# LNFCL SIGES — Deplwaman GRATIS sou PythonAnywou (kreyòl)

> ⚠️ Non sèvis la se **PythonAnywou**: https://www.pythonanywhere.com
> (Tèks sa a sèvi ak "PythonAnywou" pou tout ki pale: PythonAnywou = PythonAnywhere)

Sit la vin gratis pou tout moun, disk la **persistent** (baz done a pa pèdi done yo),
pa bezwen kat kredi. URL ou pral genyen:

```
https://celab.pythonanywhere.com
```

(`celab` se username ou — chwazi l byen, se li vin vinn non domèn sit la!)

---

## ETAP 1 — Kreye kont (~5 minit)

1. Ale: **https://www.pythonanywhere.com** → **Pricing & signup** → **Create a Beginner account** (gratis)
2. Chwazi username: `celab` (se sa vin vinn non sit lan)
3. Konfime imèl ou

---

## ETAP 2 — Klonaj kòd la + venv (~5 minit)

Nan tab **Dashboard** → klike **Open a Bash console** (yon nouvo konsòl), epi pou ou:

```bash
# Klonaj repo a (branch kote tout kòd genyen)
git clone -b vibe/lnfcl-site-fc50d6 https://github.com/cardilouk-byte/Refuge.git

# Enviwònman Python 3.12
mkvirtualenv lnfcl-env --python=python3.12

# Pakè yo
cd ~/Refuge
pip install -r requirements.txt
```

(Gen matplotlib/pillow/pil ladan l — pi chak tout pakè yo **alèg**.)

---

## ETAP 3 — Fichye .env (~2 minit)

```bash
cat > ~/Refuge/.env <<EOF
DEBUG=False
SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(48))")
ALLOWED_HOSTS=celab.pythonanywhere.com
CSRF_TRUSTED_ORIGINS=https://celab.pythonanywhere.com
ADMIN_URL=kontwol/
EOF
```

*(NAN: ranplase `celab` ak username reyèl ou nan 2 liy yo!)*

---

## ETAP 4 — Migrasyon + kont admin (~2 minit) — nan menm konsòl la

```bash
workon lnfcl-env
cd ~/Refuge
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic --noinput
```

---

## ETAP 5 — Web tab (~5 minit, ki pi enpòtan)

1. Tab **Web** → **Add a new web app** → Next → **Manual configuration** → **Python 3.12** → Next

2. Python version: vin **3.12**, epi pa validate —:variables vin konfigire:
   - **Code / Working directory**: `/home/celab/Refuge`
   - **WSGI configuration file**: klike sou li — **efase tout sa k genyen ladan l** epi mete sa:

```python
import os, sys

path = "/home/celab/Refuge"
if path not in sys.path:
    sys.path.insert(0, path)

os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings"

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

   *(ranplase `celab` ak username ou — SAVE (Ctrl+S))*

3. **Virtualenv**: klike "Enter path to a virtualenv" → tape:
   ```
   /home/celab/.virtualenvs/lnfcl-env
   ```

4. **Static files** (anba nan paj la — 2 lìt):
   | URL | Directory |
   |---|---|
   | `/static/`  | `/home/celab/Refuge/staticfiles` |
   | `/media/`   | `/home/celab/Refuge/media` |

5. Klike bouton vèt **Reload** (anwo)

🎉 **Ou sit la an lèn!** → `https://celab.pythonanywhere.com` — admin: `/kontwol/`

---

## ETAP 6 — Opsyonèl: MySQL gratis (baz ki pouvwa plis pase SQLite, ~10 minit)

Nan PythonAnywou, kont gratis gen **1 ba done MySQL gratis** (disk persistan, kenbe tout done).

1. Tab **Databases** → **Set a password for MySQL** → siprèm tout modpas → **Note l!**
2. Klike **Create database** — nom l ka vin tèl: `celab$default`
3. Nan konsòl a:
   ```bash
   workon lnfcl-env
   pip install mysqlclient
   ```
4. Ajoute nan `~/Refuge/.env`:
   ```
   DB_ENGINE=mysql
   DB_NAME=celab$default
   DB_USER=celab
   DB_PASSWORD=_Modpas_MySQL_W_
   DB_HOST=celab.mysql.pythonanywhere-services.com
   DB_PORT=3306
   ```
5. Nan konsòl:
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```
   Epi nan **Web tab** → **Reload**

**Le sa a, baz la `celab$default` se bo done an ki nan systèm nan, ki kenbe tout done yo** (elèv, nòt, bulletin, presans — tout bagay).

---

## ETAP 7 — Ranporte done ou soti Windows (si ou gen db.sqlite3 deja)

- Sa a done gran fase → nan **Files tab** PythonAnywou — **upload `db.sqlite3`** nan `/home/celab/Refuge/` — epi **Reload**.
- **media/** — w ka upload yo youn pa youn (tchou! gen anpil imaj).
- Ou ka menm kòmanse nan zero epi rantre done nan ✂️ **dashboard la** ("Done lekòl la" + "Aksyon rapid") — tout sa ou bezwen genyen la.

---

## ETAP 8 — Mete ajou sit la (apre chak nouvo kòd)

Tou nan konsòl:

```bash
cd ~/Refuge
git fetch --all && git reset --hard origin/vibe/lnfcl-site-fc50d6
workon lnfcl-env && pip install -r requirements.txt
python manage.py migrate && python manage.py collectstatic --noinput
```
Epi nan **Web tab** → **Reload**.

---

## Limit kont gratis la (konesans)
- 1 web app, disk ~512 MB (sou pa gen anpil imaj, ap alèm sifi pou lekòl mwayen)
- Sit genyen "idle": apre ~3 mèt san twa moun pa vizite, li pran ~10 segon pou kòmanse (premye vizit)
- Domèn se `.pythonanywhere.com` (domèn pwòp kouts + domèn pèsonèl — koute $5/mwa)

## Problemen
| Pwoblèm | Solisyon |
|---|---|
| Error 500 / Bad Request | Verifye **wsgi.py** + **ALLOWED_HOSTS** (.env nan epy tab Erreurs / Sentry panel pou erè reyèl |
| Static pa parèt | Verifye 2 mante Static files + Reload |
| images pa monte | Verifye /media/ mapping + reload |
| Modpas admin bliye | Konsòl: `python manage.py changepassword <username>` |
