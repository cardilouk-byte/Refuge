# LNFCL — Sit wèb dinamik Django

Sit ofisyèl **Lycée National François Cappoix de Limonade** (LNFCL).
Deviz: *« S'instruire pour mieux servir »*.

Tout kontni sit la (tèks, imaj, menu, kontak, rezilta) soti nan baz done a
epi yo modifye nan admin Django (`/admin`) — **san touche kòd**.

## Etap 1 — Preparasyon

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Pwojè a deja kreye: pwojè `config` + aplikasyon `core`.

## Etap 2 — Konfigirasyon

Nan `config/settings.py`:

- Lang: **franse**, fizo orè: **America/Port-au-Prince** (Ayiti)
- `STATIC` (CSS/JS) ak `MEDIA` (imaj/PDF admin voye)
- Context processor `core.context_processors.site_info`
  (paramèt sit + menu disponib sou tout paj)
- Redireksyon koneksyon/dekoneksyon (`LOGIN_REDIRECT_URL`, `LOGOUT_REDIRECT_URL`)

Tou: kle sekrè a soti nan fichye `.env` (pa janm commit l).
Kopye `.env.example` → `.env` epi ranpli valè ou.

## Etap 3 — Baz done

11 modèl: `SiteSettings`, `MenuItem`, `HeroSlide`, `About`, `Service`,
`Program`, `GalleryImage`, `Result`, `NewsEvent`, `TeamMember`,
`ContactMessage`.

```bash
python manage.py makemigrations
python manage.py migrate
```

## Etap 4 — Administrasyon

```bash
python manage.py createsuperuser
python manage.py seed_demo      # kontni demonstrasyon (opsyonèl)
python manage.py runserver
```

Apre sa louvri:

- Sit la: <http://127.0.0.1:8000/>
- Admin: <http://127.0.0.1:8000/admin/>

### Sa ou kapab modifye nan admin (san kòd)

| Seksyon admin | Sa w ka chanje |
| --- | --- |
| Paramètres du site | Non lekòl, logo, deviz, adrès, telefòn, imèl, rezo sosyal, Google Maps, koulè prensipal, opasite kouch ble a, vitès slider, SEO, favicon, copyright |
| Éléments de menu | Non, lyen, lòd, afiche/kache |
| Slides héro | Imaj, tit, deviz, bouton, lòd, aktif/inaktif |
| À Propos | Tèks, imaj, estatistik, mesaj direktè, misyon, vizyon |
| Services | Tit, deskripsyon, ikòn, lòd |
| Programmes | Non, deskripsyon, imaj, nivo, lòd |
| Images de galerie | Foto, tit, kategori, lòd |
| Résultats | Tit, ane eskolè, PDF, piblik oswa sèlman konekte |
| Nouvelles / Événements | Tit, imaj, tèks, piblye/pa piblye |
| Équipe / Professeurs | Non, foto, pozisyon, matyè |
| Messages de contact | Li mesaj yo, make li/pa li (lekti sèlman) |
| Utilisateurs | Kreye itilizatè, bay dwa pa modèl (ex: sèlman galri), chanje modpas |

## Etap 5-8 — Views, Templates, CSS, JS

- **Paj yo**: Accueil (hero slider + tout seksyon), Résultats, Connexion.
- **Fòm kontak**: valide, sove nan admin, opsyon imèl (`ADMIN_EMAIL_NOTIFICATION` nan `.env`).
- **JS**: slider otomatik + fle, AOS (animasyon), konte estatistik,
  header sticky, smooth scroll, lightbox galri, bouton retounen anlè.
- **CSS**: varyab koulè (`--primary: #0d6efd`), header ak vag, responsive
  (òdinatè / tablèt / telefòn), hamburger menu.

## Etap 9 — Sekirite

- Token CSRF nan tout fòm (otomatik ak Django).
- Rezilta prive vizib sèlman pou itilizatè konekte.
- Limit gwosè/tip fichye: imaj ≤ 5 Mo, PDF ≤ 10 Mo, sèlman ekstansyon ki otorize.
- `DEBUG` ak `SECRET_KEY` nan `.env` — mete `DEBUG=False` an pwodiksyon.

## Etap 10 — Tès

```bash
python manage.py test core
```

## Etap 11 — Deplwaman (rezime)

1. Chwazi hébergement (PythonAnywhere, Render, VPS).
2. Pase sou PostgreSQL (`psycopg[binary]` + `DATABASES`).
3. `ALLOWED_HOSTS` nan `.env`, `python manage.py collectstatic`.
4. Gunicorn + Nginx, HTTPS ak Let's Encrypt.
5. Sovgad otomatik baz done a.

```bash
pip install gunicorn
gunicorn config.wsgi:application --bind 0.0.0.0:8000
```

## Estrikti

```
lnfcl/
├── config/            # Pwojè Django (settings, urls, wsgi)
├── core/
│   ├── models.py      # 11 modèl (tout kontni sit la)
│   ├── admin.py       # Admin pèsonalize
│   ├── views.py       # Accueil, Résultats, fòm kontak
│   ├── forms.py       # ContactForm
│   ├── context_processors.py
│   ├── templates/core/    # base, home, results, login, partials
│   ├── static/css|js      # style.css, main.js
│   └── management/commands/seed_demo.py
├── media/             # Fichye admin voye (imaj, PDF) — pa nan repo
└── .env               # SECRET_KEY, DEBUG, ALLOWED_HOSTS (pa commit)
```
