# LNFCL — SIGES + Sit wèb dinamik

Sistèm konplè pou **Lycée National François Cappoix de Limonade**: jesyon eskolè (SIGES) + sit vitrine piblik.

Deviz: *« S'instruire pour mieux servir »*

## Sa ki ladan l

| Pati | Detay |
|---|---|
| Sit vitrine | Hero (imaj/videyo), À Propos, Sèvis, Pwogram, Galeri (foto/videyo), Nouvèl, Ekip, Rezilta PDF, Kontak |
| Pre-enskripsyon | 4 etap sou entènèt, referans otomatik, revizyon Direction, konvèsyon an elèv |
| SIGES | Elèv, Paran, Pwofesè, Klas, Matyè, Nòt, Prezans, Finans, Mesaj, Orè |
| Organigramme | Depatman ak sous-depatman (Direction, Secrétariat, RH, Bibliothèque...) + pòs pèsonèl |
| Configuration | Koulè, font, animasyon, seksyon on/off — tout nan dashboard lan |
| 4 Sant | Backup (ZIP+SHA-256), Word (DOCX/PDF reyèl), Excel (XLSX reyèl), Media (konpresyon) |

## Enstalasyon sou Windows (etap pa etap)

1. **Enstale Python 3.11+** — [python.org](https://www.python.org/downloads/) (make "Add Python to PATH")

2. **Telechaje pwojè a** epi deconpresse l, louvri **Command Prompt (cmd)**:

```cmd
cd "C:\Users\DEP_Etud2\Desktop\site web pou lekol\Refuge-vibe-lnfcl-site-fc50d6"
```

3. **Enstale pakè yo** (pa sèvi ak `pip.exe` dirèkteman — Smart App Control ka bloke l):

```cmd
python -m pip install -r requirements.txt
```

4. **Kreye baz done a** (SQLite otomatikman, pa gen konfigirasyon):

```cmd
python manage.py migrate
```

5. **Kreye kont admin ou** (swiv enstriksyon yo):

```cmd
python manage.py createsuperuser
```

6. **Chaje done demo lekòl la** (tout kòmandman idempotent — ou ka rele yo anko):

```cmd
python manage.py seed_demo
python manage.py seed_siges
python manage.py seed_documents
python manage.py seed_departments
```

7. **Lanse sit la**:

```cmd
python manage.py runserver
```

8. Louvri **http://127.0.0.1:8000/**

## Adrès enpòtan

| Adrès | Sa li ye |
|---|---|
| `/` | Sit piblik lekòl la |
| `/preinscription/` | Fòm pre-enskripsyon 4 etap (piblik) |
| `/kontwol/` | Panneau kontwòl (admin — adrès sekre, chanje l nan `.env`) |
| `/tableau/` | Dashboard jesyon (personnel lekòl) |
| `/configuration/` | Konfigirasyon sit la (Super Admin) |
| `/organigramme/` | Organigramme depatman yo |
| `/preinscriptions/` | Trakte pre-enskripsyon yo (Direction) |
| `/backup/`, `/documents/`, `/excel/`, `/medias/` | 4 sant pwodiktivite a |

## Kont demo (si w sèvi ak seed_siges)

| Kont | Modpas | Wòl |
|---|---|---|
| `admin` | `AdminLNFCL2026!` | Super Admin |
| `direction` | `Direction2026!` | Direction |
| `prof1` | `Prof2026!` | Pwofesè |
| `eleve1` | `Eleve2026!` | Elèv |
| `parent1` | `Parent2026!` | Paran |

> ⚠️ Chanje modpas sa yo anvan pwodiksyon!

## Konfigirasyon pwodiksyon (`.env`)

Kopye `.env.example` → `.env` epi ranpli:

```
SECRET_KEY=yon-long-kle-sekre-aleatwa
DEBUG=False
ALLOWED_HOSTS=lnfcl.edu.ht,www.lnfcl.edu.ht
ADMIN_URL=kontwol/

DB_ENGINE=postgres
DB_NAME=lnfcl
DB_USER=lnfcl
DB_PASSWORD=modpas-pg
DB_HOST=localhost
DB_PORT=5432
```

Apre sa:

```cmd
python manage.py migrate
python manage.py collectstatic
```

## Backup otomatik (pwodiksyon)

Pwogram backup chak jou/semèn/mwa ap mache lè `run_backups` egzekite. Sou Windows, sèvi ak **Task Scheduler**:

```
Programme: C:\Path\Vers\Python\python.exe
Arguments: C:\Path\Vers\Pwojè\manage.py run_backups
```

Sou Linux (cron): `0 2 * * * /usr/bin/python3 /path/to/manage.py run_backups`

## Pwoblèm komen

| Pwoblèm | Solisyon |
|---|---|
| `pip.exe was blocked by Device Guard` | Sèvi ak `python -m pip install -r requirements.txt` |
| Erè "no such table" / fòm pa sove | Fè `python manage.py migrate` |
| Imaj/videyo pa parèt | Fè `migrate` epi verifye fichye a < 15 Mo (imaj) / < 150 Mo (videyo, MP4 pi bon) |
| Déconnexion pa mache | Re-telechaje dènye vèsyon an (fòm POST kounye a) |
| `ModuleNotFoundError` | `python -m pip install -r requirements.txt` |

## Tès

```cmd
python manage.py test
```
