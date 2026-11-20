import hashlib
import io
import zipfile
from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from openpyxl import Workbook, load_workbook

from backups import services
from backups.models import BackupRecord, BackupSettings
from document_editor.models import Document, DocumentTemplate
from excel_manager.imports import import_students
from media_library.models import MediaFile
from students.models import Student

User = get_user_model()


def _png_file():
    from PIL import Image
    buffer = BytesIO()
    Image.new("RGB", (2000, 1200), (13, 110, 253)).save(buffer, format="PNG")
    return SimpleUploadedFile("test.png", buffer.getvalue(), content_type="image/png")


def _xlsx_file(headers, rows):
    wb = Workbook()
    ws = wb.active
    ws.append(headers)
    for row in rows:
        ws.append(row)
    buffer = BytesIO()
    wb.save(buffer)
    return SimpleUploadedFile("test.xlsx", buffer.getvalue(),
                              content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


class BackupTests(TestCase):
    def setUp(self):
        self.superadmin = User.objects.create_user(
            username="root", password="test1234!", role=User.Role.SUPERADMIN,
            is_staff=True, is_superuser=True,
        )
        self.staff = User.objects.create_user(
            username="dir1", password="test1234!", role=User.Role.DIRECTION, is_staff=True,
        )
        BackupSettings.objects.get_or_create(pk=1)

    def test_create_backup_makes_zip_with_checksum(self):
        record = services.create_backup(user=self.superadmin)
        self.assertEqual(record.status, BackupRecord.Status.SUCCESS)
        path = services.BACKUP_DIR / record.filename
        self.assertTrue(path.exists())
        with zipfile.ZipFile(path) as zf:
            self.assertIn("data.json", zf.namelist())
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), record.checksum)

    def test_verify_backup_detects_integrity(self):
        record = services.create_backup(user=self.superadmin)
        ok, message = services.verify_backup(record)
        self.assertTrue(ok)
        record.checksum = "0" * 64
        record.save()
        ok, message = services.verify_backup(record)
        self.assertFalse(ok)

    def test_restore_backup_restores_data(self):
        services.create_backup(user=self.superadmin)
        Student.objects.create(matricule="ELV-BKP-001", first_name="Avant", last_name="Backup")
        record = BackupRecord.objects.first()
        services.restore_backup(record)
        self.assertFalse(Student.objects.filter(matricule="ELV-BKP-001").exists())

    def test_only_superadmin_can_create_backup(self):
        self.client.login(username="dir1", password="test1234!")
        response = self.client.post(reverse("backups:create"))
        self.assertEqual(response.status_code, 403)
        self.client.login(username="root", password="test1234!")
        response = self.client.post(reverse("backups:create"))
        self.assertRedirects(response, reverse("backups:index"))

    def test_import_backup_zip_restores_data(self):
        from django.core.files.uploadedfile import SimpleUploadedFile

        # 1. F yon backup
        record = services.create_backup(user=self.superadmin)
        path = services.BACKUP_DIR / record.filename

        # 2. Ajoute done NOUVÈO apre backup la (dwe efase pa restore a)
        Student.objects.create(matricule="ELV-IMP-001", first_name="Apre", last_name="Import")

        # 3. Importe ZIP la (jan yon itilizatè telechaje l + re-upload l ta fè)
        with open(path, "rb") as fh:
            uploaded = SimpleUploadedFile("backup_test.zip", fh.read(), content_type="application/zip")
        self.client.login(username="root", password="test1234!")
        response = self.client.post(
            reverse("backups:import"),
            {"backup_file": uploaded, "media": "on"},
            format="multipart",
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Student.objects.filter(matricule="ELV-IMP-001").exists())  # restore absolve

        # 4. Backup la anrejistre nan listwa
        self.assertTrue(BackupRecord.objects.filter(note__contains="import").exists() or
                        BackupRecord.objects.filter(filename__contains="_import.zip").exists())

    def test_import_rejects_non_lnfcl_zip(self):
        from django.core.files.uploadedfile import SimpleUploadedFile

        # ZIP ki pa gen data.json → refize
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as zf:
            zf.writestr("random.txt", "hello")
        self.client.login(username="root", password="test1234!")
        uploaded = SimpleUploadedFile("fake.zip", buffer.getvalue(), content_type="application/zip")
        response = self.client.post(
            reverse("backups:import"),
            {"backup_file": uploaded},
            format="multipart",
        )
        self.assertEqual(response.status_code, 302)
        # pa gen _import.zip ki rete nan backups_store
        leftovers = list(services.BACKUP_DIR.glob("backup_*_import.zip"))
        self.assertEqual(leftovers, [])

    def test_import_rejects_non_zip_file(self):
        from django.core.files.uploadedfile import SimpleUploadedFile

        # ensure dir exists
        BackupSettings.objects.get_or_create(pk=1)
        self.client.login(username="root", password="test1234!")
        uploaded = SimpleUploadedFile("fichier.txt", b"not a zip", content_type="text/plain")
        response = self.client.post(
            reverse("backups:import"),
            {"backup_file": uploaded},
            format="multipart",
        )
        self.assertEqual(response.status_code, 302)

    def test_import_requires_superadmin(self):
        self.client.login(username="dir1", password="test1234!")
        response = self.client.post(reverse("backups:import"))
        self.assertEqual(response.status_code, 403)

    def test_backup_page_accessible_to_staff(self):
        self.client.login(username="dir1", password="test1234!")
        response = self.client.get(reverse("backups:index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Backup Center")


class DocumentEditorTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(
            username="dir1", password="test1234!", role=User.Role.DIRECTION, is_staff=True,
        )
        DocumentTemplate.objects.get_or_create(
            name="Attestation test", category="ATTESTATION",
            defaults={"body_html": "<h1>ATTESTATION</h1><p>{Nom}</p>"},
        )

    def test_editor_save_and_docx_export(self):
        self.client.login(username="dir1", password="test1234!")
        response = self.client.post(reverse("document_editor:create"), {
            "title": "Test attestation", "category": "ATTESTATION",
            "body_html": "<h1>Titre</h1><p>Texte <strong>gras</strong></p>"
                         "<table><tr><th>A</th><th>B</th></tr><tr><td>1</td><td>2</td></tr></table>",
            "watermark": "BROUILLON", "action": "stay",
        })
        self.assertEqual(response.status_code, 302)
        document = Document.objects.get(title="Test attestation")
        response = self.client.get(reverse("document_editor:export_docx", args=[document.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertIn("wordprocessingml", response["Content-Type"])
        from docx import Document as DocxDocument
        doc = DocxDocument(io.BytesIO(response.content))
        texts = "\n".join(p.text for p in doc.paragraphs)
        self.assertIn("Titre", texts)
        self.assertTrue(any(table.rows for table in doc.tables))

    def test_pdf_export(self):
        document = Document.objects.create(
            title="Rapport", category="RAPPORT",
            body_html="<h1>Rapport</h1><p>Contenu</p>", watermark="COPIE",
        )
        self.client.login(username="dir1", password="test1234!")
        response = self.client.get(reverse("document_editor:export_pdf", args=[document.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertTrue(response.content.startswith(b"%PDF"))

    def test_templates_seeded(self):
        self.client.login(username="dir1", password="test1234!")
        response = self.client.get(reverse("document_editor:index"))
        self.assertContains(response, "Attestation test")


class ExcelManagerTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(
            username="dir1", password="test1234!", role=User.Role.DIRECTION, is_staff=True,
        )

    def test_import_students_creates_and_detects_errors(self):
        file = _xlsx_file(
            ["Matricule", "Prénom", "Nom", "Sexe (M/F)", "Date naissance (AAAA-MM-JJ)",
             "NIS", "NINU", "Adresse", "Classe"],
            [
                ["ELV-IMP-001", "Jean", "Pierre", "M", "2010-05-01", "", "", "", ""],
                ["", "", "Incomplet", "", "", "", "", "", ""],
            ],
        )
        result = import_students(file)
        self.assertEqual(result["created"], 1)
        self.assertEqual(len(result["errors"]), 1)
        self.assertTrue(Student.objects.filter(matricule="ELV-IMP-001").exists())

    def test_import_students_is_idempotent(self):
        file = _xlsx_file(
            ["Matricule", "Prénom", "Nom", "Sexe (M/F)", "Date naissance (AAAA-MM-JJ)",
             "NIS", "NINU", "Adresse", "Classe"],
            [["ELV-IMP-002", "Marie", "Louis", "F", "", "", "", "", ""]],
        )
        import_students(file)
        result = import_students(file)
        self.assertEqual(result["created"], 0)
        self.assertEqual(result["updated"], 1)

    def test_export_students_xlsx(self):
        Student.objects.create(matricule="ELV-EXP-001", first_name="Test", last_name="Export")
        self.client.login(username="dir1", password="test1234!")
        response = self.client.get(reverse("excel_manager:export_students"))
        self.assertEqual(response.status_code, 200)
        wb = load_workbook(BytesIO(response.content))
        rows = list(wb.active.iter_rows(values_only=True))
        self.assertEqual(rows[0][0], "Matricule")
        self.assertTrue(any("ELV-EXP-001" in [str(c) for c in row] for row in rows[1:]))

    def test_excel_center_requires_staff(self):
        User.objects.create_user(username="parent1", password="test1234!", role=User.Role.PARENT)
        self.client.login(username="parent1", password="test1234!")
        response = self.client.get(reverse("excel_manager:index"))
        self.assertEqual(response.status_code, 403)


class MediaLibraryTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(
            username="dir1", password="test1234!", role=User.Role.DIRECTION, is_staff=True,
        )

    def test_upload_compresses_image(self):
        self.client.login(username="dir1", password="test1234!")
        uploaded = _png_file()
        response = self.client.post(reverse("media_library:upload"), {
            "files": [uploaded], "category": "SITE",
        })
        self.assertRedirects(response, reverse("media_library:index"))
        media = MediaFile.objects.first()
        self.assertIsNotNone(media)
        self.assertTrue(media.file.name.endswith(".jpg"))
        self.assertLess(media.size_bytes, 500 * 1024)
        self.assertEqual(media.width, 1600)

    def test_library_requires_staff(self):
        response = self.client.get(reverse("media_library:index"))
        self.assertEqual(response.status_code, 302)
