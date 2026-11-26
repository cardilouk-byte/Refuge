from django.core.management.base import BaseCommand

from departments.models import Department


STRUCTURE = [
    ("Direction Générale", "DIR", "DIRECTION", None, "Directeur Général"),
    ("Secrétariat", "SEC", "ADMINISTRATION", "Direction Générale", "Secrétaire de Direction"),
    ("Comptabilité / Finances", "FIN", "ADMINISTRATION", "Direction Générale", "Comptable"),
    ("Ressources Humaines", "RH", "ADMINISTRATION", "Direction Générale", "Responsable RH"),
    ("Scolarité / Inscriptions", "SCL", "ADMINISTRATION", "Direction Générale", "Responsable Scolarité"),
    ("Enseignement", "ENS", "PEDAGOGIQUE", None, "Directeur des Études"),
    ("Préscolaire", "PRE", "PEDAGOGIQUE", "Enseignement", "Responsable Préscolaire"),
    ("Fondamental (1ère-6ème AF)", "FON", "PEDAGOGIQUE", "Enseignement", "Responsable Fondamental"),
    ("Secondaire (7ème-9ème AF)", "SEC2", "PEDAGOGIQUE", "Enseignement", "Responsable Secondaire"),
    ("Nouveau Secondaire (NS1-NS4)", "NS", "PEDAGOGIQUE", "Enseignement", "Responsable Nouveau Secondaire"),
    ("Bibliothèque", "BIB", "APPUI", None, "Bibliothécaire"),
    ("Discipline / Surveillance", "DIS", "APPUI", None, "Chef de Discipline"),
    ("Informatique", "INF", "APPUI", None, "Responsable Informatique"),
    ("Maintenance & Logistique", "MTN", "APPUI", None, "Responsable Maintenance"),
    ("Infirmerie", "IRI", "APPUI", None, "Infirmier(ère)"),
]


class Command(BaseCommand):
    help = "Kreye estrikti depatman lekòl la (organigramme)."

    def handle(self, *args, **options):
        created = 0
        for order, (name, code, kind, parent_name, head_title) in enumerate(STRUCTURE, start=1):
            parent = None
            if parent_name:
                parent = Department.objects.filter(name=parent_name).first()
            _, was_created = Department.objects.update_or_create(
                code=code,
                defaults={
                    "name": name, "kind": kind, "parent": parent,
                    "head_title": head_title, "order": order, "is_active": True,
                },
            )
            if was_created:
                created += 1
        self.stdout.write(self.style.SUCCESS(f"Organigramme OK — {created} nouvo depatman kreye."))
