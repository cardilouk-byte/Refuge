import os

from django.core.management.base import BaseCommand
from django.db import models


class Command(BaseCommand):
    help = "Verifye si tout imaj ak fichye nan baz done a egziste vre nan dosye media/ la."

    def handle(self, *args, **options):
        from config.settings import MEDIA_ROOT

        missing = 0
        total = 0
        for model in self._models_with_files():
            for obj in model._meta.default_manager.all():
                for field in model._meta.get_fields():
                    if not isinstance(field, models.FileField):
                        continue
                    name = getattr(obj, field.name).name
                    if not name:
                        continue
                    total += 1
                    path = os.path.join(MEDIA_ROOT, name)
                    if not os.path.isfile(path):
                        missing += 1
                        self.stdout.write(self.style.ERROR(
                            f"MANKE: {model.__name__} #{obj.pk} ({field.name}) -> media/{name}"
                        ))
        self.stdout.write("")
        self.stdout.write(f"Fichye verifye: {total} | ki manke: {missing}")
        if missing:
            self.stdout.write(self.style.WARNING(
                "Konsèy: kopye ansyen dosye media/ ou a nan dosye pwojè a (kote manage.py ye), apre sa reeseye."
            ))
        else:
            self.stdout.write(self.style.SUCCESS("Tout fichye yo bon!"))

    def _models_with_files(self):
        from django.apps import apps
        for model in apps.get_models():
            if any(isinstance(f, models.FileField) for f in model._meta.get_fields()):
                yield model
