# SPEC-CONFORMITE — LNFCL SIGES

Tablo korespondans ant espesifikasyon pwofesyonèl la (19 seksyon) ak sa ki egziste nan pwogram nan.

Legand: **FÈT** = fonksyonèl epi opere · **PASYÈL** = pwensipal la fèt, yon detay manke · **PLANIFIE** = poko fèt.

## 1. Tableau de bord — FÈT
- 7 kat statistik: elèv aktif, pwofesè, klas, matye, paran, inskri ane a, pré-inscriptions admis/rejetés — `/tableau/`
- Finans (facturé, encaisse, depans, bilan, fakti poko peye) — kat + `/finance/`
- Assiduité (taux presans + PRESENT/ABSENT/RETARD) — kat
- Grafik Chart.js: mwayèn pa matiyè pou peryòd aktyèl
- Aktivite resan (peman resan) + notifikasyon mwen + dènye enskripsyon + dènye nòt

## 2. Gestion elèv — FÈT
- Enskripsyon elèv pa klas: CRUD konplè nan dashboard (Elèv yo)
- Dosye endividyèl: foto, infos paran (ParentStudent), adrès, Kat idantite QR `/badge/`
- Status + pasaj ane `/nouvel-ane/` (vin / mantni / redouble / kite) — pa rekòmanse pou nouvo ane
- Rechèch pa non, matricule, klas
- Impression fich: Kat idantite (print CSS) — FÈT; fich PDF konplè = PLANIFIE
- **Fiche d'inscription (FÈT)**: après konvèti yon pré-inscription, sistèm nan redireksyon dirèkteman sou `/preinscriptions/<pk>/fich-inskripsyon/` (FICHE D'INSCRIPTION A4 print: elèv, matricule, paran, klas, siyati) — lyen tou nan detay pré-inscription

## 3. Structure éducative MENFP — FÈT
- SchoolYear / Cycle / Level / ClassRoom / Period: Préscolaire, 1e–9e AF, Secondaire 1–4 (seed `seed_siges`)
- CRUD nivo, klas, seksyon, ane, peryòd nan dashboard (Done lekòl la)
- Matye + ClassSubject (koeficien) + ScheduleSlot — UI kalendriye vizyèl = PLANIFIE

## 4. Gestion pwofesè / pèsonèl — PASYÈL
- FÈT: dosye pwofesè + asiyman kote (CRUD), depans SALAIRE, presence pwofesè via app elèv
- PASYÈL: ScheduleSlot egziste — kalendriye vizyèl, diplòm/kontra/konje = PLANIFIE

## 5. Not & Bulletins — FÈT
- Saisie `/notes/klas/<pk>/` pa klas + peryòd (interro / devoir / examen, koeficien)
- Mwayèn otomatik: `subject_average`, `general_average` (koeficien), `class_ranking`, <b>/10</b>
- Desizyon peryòd: ADMIS / AVÈTISMAN / REDOUBLE / ECHOUE — bulletin klas + sik
- Tablo donè `/notes/tablo-done/` — 10 pi bon elèv (mwayèn >= 10) tout klas kole
- Bulletin otomatik + impression (print CSS); PDF WeasyPrint = PLANIFIE
- Paywall: elèv poko peye fakti a → bulletin bloke (`_bulletin_locked`)
- Historique pa sik; grafik evolisyon dedye = PLANIFIE
- **Karnè lekòl = vrè LIVRET A5 (FÈT)**: modèl modifiable (kouvèti, slogan, adrès, tèl, deviz, règman entèn, direktè, koulè kadajyè, foto) sou `/notes/carnet/model/` ; apèsi A5 2 mòd sou `/notes/carnet/eleve/<pk>/` — **lekti** (viewer kst ap vire paj: prev/next/flech) ak **livret** (2 paj A5 sou fey A4 landscape, entepozisyon otomatik [8,1][2,7][6,3][4,5], paj vid otomatik pou miltip de 4) ; **PDF ReportLab** `/notes/carnet/eleve/<pk>/pdf/?mod=livret|lekti` (nimewotasyon, tab multi-paj, graf sikilè NS4/9e AF) ; **pĭ lot** tout klas: `/notes/carnet/klas/<pk>/pdf/?mod=livret` ; paj: kouvèti devan, règman, idantifikasyon+siyati+kachèt, tab MATIÈRES×COEF×syik peryòd×Notes Globales×prof, Total koef/pwen/elèv/klas/Rang/Mention/Décision, Obsèvasyon, kouvèti dèyè. **VALIDASYON PEMAN (FÈT)**: karnè a gade tout fakti elèv la otomatikman — si yon sèl fakti poko PAYE (impayée oswa pasyèl), chak paj pote filigran wouj «NON VALIDÉ» + piti badge «SYIK PAKA VALIDE» sou chak fèy nòt (syik pa syik) ; lè tout frè yo peye (espès, MonCash, chèk, vireman bank BNC/BHD/Sogebank, koperativ kredi) tampon vèt «VALIDÉ — DIRECTION» parèt sou idantifikasyon/nòt/rezilta + badge «SYIK VALIDE» ; elèv/PARENN ki poko peye jwenn paj blok `/notes/carnet/eleve/<pk>/` ak lis mwayen peman (staff ka toujou gade apèsi a).

## 6. Presans & absans — FÈT
- Chak jou: `/presens/` → take(clas) PRESENT / ABSENT / RETARD + justifie + note
- Rapor `/presens/rapor/` (+ filte klas, elèv, dat) + eksport Excel
- Notifikasyon paran OTOMATIK lè elèv ABSENT (Notification.send_many)
- Cahier de vérification: app cahiers (mojo, sal)

## 7. Financière — FÈT
- FeeType + Invoice IMPAYE / PARTIEL / PAYE (update_status otomatik)
- Peman pasyèl + dettes: Payment (MonCash / NatCash / Espèces / Bank / Chèque), kuitala REC-000001, resi imprimable
- Depans (5 catégorie) — `/finance/depans/`
- Balans (revni - depans) nan tablo finansye + aktivite resan
- Salaires automatik = PLANIFIE

## 8. Archives & documents — FÈT
- Backup ZIP + SHA-256 + verify + restore konplè — `/backup/` (+ `run_backups` otomatik)
- IMPORT + RESTORE yon ZIP ki te telechaje anvan — `/backup/backup/importer/` (verify ZIP + data.json, ranplase done, rezilta nan listwa)
- Media Library `/medias/`, Document Editor Word `/documents/` (10 templates, watermark), Excel `/excel/`
- Bulletins/archive annyennes konservé pa SchoolYear; OCR = PLANIFIE

## 9. Portail paran — FÈT
- Tout (nòt, devoirs, précens, quiz, examens, bulletin) scoping otomatik pa ParentStudent
- Notifikasyon obsans + cloche navbar; bulletin paywall active pou tout visit
- Reçu téléchargé/imprimable — finance:payment_receipt

## 10. Portail élève — FÈT
- Profil + Kat idantite QR `/badge/` (+ verifikasyon public `/badge/verifie/<matricule>/`)
- Nòt, mwayèn, bulletin (paywall peyman)
- Devoirs, examens, quiz, presans — lise scoping pa pwofesè
- Dépôt devoir (upload) = PLANIFIE

## 11. Bibliothèque — FÈT
- Book (kategori, auteur, egzemplaires) + Loan (emprunt, retour, is_late)
- Guard: pa gen egzemplar disponib → refize otomatik
- Historique prèt aktif + admin; pénalités = PLANIFIE

## 12. Gestion administrative — PASYÈL
- FÈT: Pré-inscription 4 étapes (wizard) + admissons (set_status) + konvètisyon an elèv matrikulé
- FÈT: Organigramme 14 depatman hiérarchisé; Document Editor pou atestation/certifikats
- PASYÈL: Exam modul (peryòd, durè, koeficien, barè) — organisasyon d'examens ofisysèls = PLANIFIE
- PLANIFIE: kalendrier réunion/événements, decisions administratives dédicates

## 13. Utilisateurs & permissions — FÈT
5 ròl: SUPERADMIN (kontrole total + Configuration + Modèl sit + Django admin), DIRECTION (gestion totale san Configuration), ENSEIGNANT (nòt, presans, devoir, cahiers, quiz, Excel), ELÈVE (test scoping), PARENT (scoping chimins).

Aksès admin:
- Django admin `/kontwol/` — SUPERADMIN séllement (pa VISIBLE)
- Dashboard web `/tableau/` — tout modúl (configuration séllement superadmin)

## 14. Graphiques & statistiques — FÈT
- Mwayèn pa matiyè (bar chart)
- Taux presans + COUNT PRESENT/ABSENT/RETARD
- Statistik finans (revni / depans / bilan)
- Repartition sexe/nivéau grafik dedye = PLANIFIE; Eksport Excel FÈT (Excel Centre)

## 15. Personnalisation sans code — FÈT
- Configuration: 7 tab (general / social / apparence / animations / seksyon / SEO / sekurité)
- Logo, couleurs (header/footer/texte/gradient), fonts (10), gradient header, style coins, animations, marquee, footer logos, maintenance
- 20 thèmes prêts `/configuration/model-sit/` — 1 klike "Aplike"
- Tout kontenu vitrine (slides, apropos, services, pwogram, galeri, nouvèl, ekip, résultats, meni) — CRUD DB

## 16. Sauvegarde & sécurité — FÈT
- Backup otomatik + manuel (ZIP + SHA-256) + restore konplè
- Admin kaché (ADMIN_URL env) + custom login branding "LNFCL - Panneau de contrôle"
- role_required / staff / teaching / superadmin decorators — 403 si pa otorize
- Maintenance middleware (503, bypass staff)
- Journal des connexions = PLANIFIE

## 17. Architecture menus sidebar — FÈT

    JENERAL        → Tableau de bord
    ÉTABLISSEMENT  → Elève yo / Matye / Pwofesè / Ané / Klas
    KLAS & KOUR    → Nòt & Bulletins · Tablo donè · Presans · Cahier kour · Quiz · Bibliothèques
    FINANCES       → Finans · Fakti & peman · Depans
    TOTALITE LEKÒL → Backup
    PRODUCTIVITÉ   → Word · Excel · Medya · Organigramme · Pré-inscriptions
    SITE WEB       → Configuration · Modèl sit (superadmin)

Tout modúl gen relasyon DB: Student -> ClassRoom -> Level -> Cycle -> SchoolYear; Grade -> ClassSubject -> Subject; Invoice -> Student + FeeType; Devoir -> ClassRoom + Subject + Teacher; Loan -> Book + Student; AttendanceRecord -> Student.

## 18. Teknoloji — FÈT
Django 6.1 (backend), Bootstrap 5.3 + Icons (UI), Chart.js (grafik), OpenPyXL (Excel), python-docx (Word), ReportLab (PDF), Pillow (imaj), qrcode (badje), SQLite / MySQL / PostgreSQL (DB_ENGINE env).

## 19. Fonctionnalités avancées — PASYÈL
- FÈT: multi-années (archive pa SchoolYear), import Excel intelligent (rapport d'érreurs), génération Word personalisé, examens
- PASYÈL: méssagerie interne (Notification, interne), historique modifs (created_by)
- PLANIFIE: multi-écoles, OCR, mode hors ligne (PWA), API, chat temps réel, journal complet

---
Dènye mize: finance-UI / presans-paran-notif / tablo-donè / dashboard-stats / spec-conformité.
