# LNFCL SIGES — Gid Deplwaman sou VPS Ubuntu (kreyòl)

Gid sa a fè w ka mete sit SIGES la sou yon VPS Ubuntu atravè **yon sèl script**, ak
Nginx + Gunicorn + PostgreSQL + HTTPS gratis.

---

## 1. Preparasyon (~5 minit)

1. Yon **VPS Ubuntu 24.04** (Vultr, DigitalOcean, Hetzner, Contabo... ~4-8 USD/mwa, 1 vCPU / 1-2 GB RAM sifi pou on lekòl mwayen).
   Si sèvè a gen sèlman 1GB RAM, ajoute **swap 2GB** d'abord:
   ```bash
   fallocate -l 2G /swapfile && chmod 600 /swapfile && mkswap /swapfile && swapon /swapfile
   echo '/swapfile none swap sw 0 0' >> /etc/fstab
   ```
2. Konekte: `ssh root@IP_SÈVÈ`

---

## 2. Enstalasyon — yon sèl kòmand

Kopye dosye `deploy/` yo sou sèvè a (oswa klonaj repo a) epi:

```bash
sudo bash install_lnfcl.sh
```

Script la mande w 3 kesyon (domèn, imèl, modpas baz done) — apre l fe tout:
pakè → PostgreSQL → klonaj GitHub → venv + pakè → `.env` sekirize → migrasyon →
collectstatic → sèvis Gunicorn (otomatikman kòmanse) → Nginx + fwouwal (ufw).

Apre li fini, **kreye kont SIPÈADMIN lan**:

```bash
cd /opt/lnfcl && sudo -u lnfcl -E ./venv/bin/python manage.py createsuperuser
```

Louvri `http://celab.eu.org/` → sit la an lèn! Admin: `http://celab.eu.org/kontwol/`.

---

## 3. Sètifikat HTTPS GRATIS (Let's Encrypt)

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d domèn-w -m imèl-w --agree-tos --redirect
```

Lè sa a nan `/opt/lnfcl/.env` chanje:
```
SECURE_SSL_REDIRECT=true
```
epi: `sudo systemctl restart lnfcl`

Renouvèlman otomatikman (test: `sudo certbot renew --dry-run`).

---

## 4. Domèn (kesyon "**.edu gratis**" ou te poze a)

⚠️ **Verite a**: yon domèn **.edu ou .edu.ht ki gratis** pa egziste reyèlman.

| Opsyon | Ki jan w jwenn li | Pri |
|---|---|---|
| **celab.eu.org** | `eu.org` — vrè domèn gratis (validasyon apeprè 1-4 semèn) | **Gratis** ✅ |
| **lnfcl.edu.ht** | `www.nic.ht` — rejis a Ayiti | peye (~30-70 USD/an) — sèl fason reyèl pou genyen **.edu.ht** |
| Domèn peye (.com, .org...) | Namecheap, Porkbun, Cloudflare | ~10 USD/an |
| Subdomèn Cloudflare/Vercel | ou pèsonèlman regjistre l | Gratis |

### Si ou chwazi **eu.org** (rekòmande pou gratis):
1. Ale `https://nic.eu.org` → kreye kont → "New domain" → mande `celab.eu.org`
2. Ou bezwen **DNS host** gratis: kreye yon kont [Cloudflare](https://cloudflare.com) (gratis), ajoute zon
   `celab.eu.org`, pran 2 sèvè DNS Cloudflare yo, ba yo nan fòm nan eu.org
3. Nan Cloudflare: rekò A `@` → IP sèvè VPS w la, rekò A `www` → menm IP (mode: DNS only)
4. Kite valdasyon eu.org pase (1-4 semèn) — script la deja pres pou l

### Rekò DNS (menm jan pou nenpòt rejistratè):
```
A    @      <IP_VPS>
A    www    <IP_VPS>
```

---

## 5. Ranporte done lekòl ou (Windows → VPS)

Si ou gen deja `db.sqlite3` + `media/` sou PC w:

```powershell
# Windows PowerShell (soti nan folder pwojè a)
scp db.sqlite3 root@IP_SÈVÈ:/opt/lnfcl/
scp -r media root@IP_SÈVÈ:/opt/lnfcl/
```

Epi sou sèvè a (enpòte SQLite → PostgreSQL):
```bash
cd /opt/lnfcl && source venv/bin/activate   # tanporè: mete DB_ENGINE=sqlite nan .env lan pou li li db.sqlite3 nan
python manage.py dumpdata --exclude contenttypes --exclude auth.permission > data.json
# mete DB_ENGINE=postgres nan .env
python manage.py migrate && python manage.py loaddata data.json
rm data.json && sudo systemctl restart lnfcl
```

---

## 6. Mete ajou vèsyon an (apre chak nouvo kòd)

```bash
sudo bash deploy/update_lnfcl.sh
```

## 7. Kòmand ijans

| Pwoblèm | Kòmand |
|---|---|
| Sit pa reponn | `sudo systemctl status lnfcl` |
| Wè erè | `sudo journalctl -u lnfcl -n 50 --no-pager` |
| Repran sèvis | `sudo systemctl restart lnfcl` |
| Repran Nginx | `sudo systemctl reload nginx` |
| Verifye Nginx | `sudo nginx -t` |
| Test e-mail/visa | `curl -I http://localhost` (nan sèvè a) |

## 8. Sekirite rekòmande paske sa se yon lekòl
- `/opt/lnfcl/.env` mòd `600`
- Pa mòd DEBUG=False detèminan apre migrations
- `ADMIN_URL` yon lòt bagay pase "kontwol/" si ou vle
- Backup rejilye: modèl Backup Center la (ZIP + SHA-256) deja nan sit la
- Fwouwal: `sudo ufw enable` (script la deja louvri 80/443 + SSH)
