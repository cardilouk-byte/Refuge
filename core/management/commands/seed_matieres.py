from django.core.management.base import BaseCommand

from academics.models import Subject

# 1\u00e8 SEKSYON \u2014 Fondamantal 1AF\u20139AF (n\u00e8curikol\u00fam MENFP)
SECTION_1 = [
    ("Cr\u00e9ole", "KRE"),
    ("Fran\u00e7ais", "FR"),
    ("Math\u00e9matiques", "MATH"),
    ("Sciences de la Nature", "SNA"),
    ("Sciences Sociales", "SOC"),
    ("\u00c9ducation \u00e0 la Citoyennet\u00e9", "ECY"),
    ("\u00c9ducation de la Vie", "EDV"),
    ("Anglais", "ANG"),
    ("Espagnol", "ESP"),
    ("\u00c9ducation Physique", "EPS"),
    ("Arts Plastiques", "ART"),
    ("\u00c9ducation Musicale", "MUS"),
    ("Conduite", "COND"),
    ("Travaux Manuels", "TM"),
]

# 2\u1d49 SEKSYON \u2014 Secondaire NS1\u2013NS4 (dapre mod\u00e8l karn\u00e8 a)
SECTION_2 = [
    ("Fran\u00e7ais I", "FR1"),
    ("Culture Litt\u00e9raire", "CLIT"),
    ("Alg\u00e8bre", "ALG"),
    ("G\u00e9om\u00e9trie", "GEO"),
    ("Trigonom\u00e9trie", "TRIG"),
    ("Chimie", "CHIM"),
    ("Physique", "PHYS"),
    ("Biologie", "BIO"),
    ("Philosophie", "PHILO"),
    ("Histoire", "HIST"),
    ("G\u00e9ographie", "GEOG"),
    ("Sciences \u00c9conomiques", "SECO"),
]


class Command(BaseCommand):
    help = "Krey\u00e8 kat\u00e8g maty\u00e8 lek\u00f2l la (1\u00e8 seksyon fondamental + 2\u1d49 seksyon secondaire)."

    def handle(self, *args, **options):
        created = 0
        for name, code in SECTION_1 + SECTION_2:
            _, is_created = Subject.objects.get_or_create(
                name=name, defaults={"code": code}
            )
            if is_created:
                created += 1
        self.stdout.write(self.style.SUCCESS(
            f"{created} maty\u00e8 nouvo kreye ({Subject.objects.count()} total). "
            "Apre sa, al nan Dashboard > Done lek\u00f2l la > Maty\u00e8 pa klas pou mete chak maty\u00e8 "
            "av\u00e8k pwofes\u00e8 ak koyefisyan li pou chak klas."
        ))
