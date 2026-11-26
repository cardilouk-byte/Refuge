from django.core.management.base import BaseCommand

from document_editor.models import DocumentTemplate

TEMPLATES = [
    ("LETTRE", "Lettre administrative", "LNFCL — Lettre officielle",
     "<p>{Ville}, le {Date}</p>"
     "<p><strong>Objet :</strong> {Objet}</p>"
     "<p>Monsieur / Madame,</p>"
     "<p>Par la présente, nous vous informons que {Contenu de la lettre}.</p>"
     "<p>Veuillez agréer, Monsieur / Madame, l'expression de nos salutations distinguées.</p>"
     '<p style="text-align: right"><strong>La Direction</strong></p>'),
    ("ATTESTATION", "Attestation de fréquentation", "LNFCL — Attestation",
     '<h2 style="text-align: center">ATTESTATION</h2>'
     "<p>Nous, soussignés, Direction du {Nom de l'école}, attestons que :</p>"
     '<p style="text-align: center"><strong>{Prénom et Nom}</strong>, né(e) le {Date de naissance},</p>'
     "<p>est régulièrement inscrit(e) en classe de {Classe} pour l'année scolaire {Année}.</p>"
     "<p>La présente attestation est délivrée pour servir et valoir ce que de droit.</p>"
     '<p style="text-align: right"><strong>Le Directeur</strong></p>'),
    ("CERTIFICAT", "Certificat de fin d'études", "LNFCL — Certificat",
     '<h2 style="text-align: center">CERTIFICAT</h2>'
     "<p>Le présent certificat est décerné à</p>"
     '<h3 style="text-align: center">{Prénom et Nom}</h3>'
     "<p>pour avoir complété avec succès le programme de {Niveau} de l'année {Année}.</p>"
     '<p style="text-align: right"><strong>La Direction</strong></p>'),
    ("BULLETIN", "Bulletin trimestriel", "LNFCL — Bulletin",
     '<h2 style="text-align: center">BULLETIN SCOLAIRE</h2>'
     "<p>Élève : <strong>{Prénom et Nom}</strong> — Classe : {Classe} — Période : {Période}</p>"
     "<table><tr><th>Matière</th><th>Moyenne</th><th>Coef.</th><th>Appréciation</th></tr>"
     "<tr><td>{Matière 1}</td><td>{Note}</td><td>{Coef}</td><td>{Appréciation}</td></tr>"
     "<tr><td>{Matière 2}</td><td>{Note}</td><td>{Coef}</td><td>{Appréciation}</td></tr></table>"
     "<p><strong>Moyenne générale :</strong> {Moyenne} / 20 — Rang : {Rang}</p>"),
    ("CONVOCATION", "Convocation parents", "LNFCL — Convocation",
     "<p>{Ville}, le {Date}</p>"
     "<p>À l'attention de : <strong>{Nom du parent}</strong></p>"
     "<p>Objet : <strong>Convocation</strong></p>"
     "<p>Nous avons l'honneur de vous convoquer à une rencontre concernant votre enfant "
     "{Nom de l'élève}, le {Date de la rencontre} à {Heure}, au bureau de la direction.</p>"
     "<p>Votre présence est vivement souhaitée.</p>"
     '<p style="text-align: right"><strong>La Direction</strong></p>'),
    ("CONTRAT", "Contrat d'engagement", "LNFCL — Contrat",
     '<h2 style="text-align: center">CONTRAT D\'ENGAGEMENT</h2>'
     "<p>Entre : <strong>{Nom de l'école}</strong>, représentée par {Nom du directeur},</p>"
     "<p>et : <strong>{Nom de l'employé}</strong>, occupant le poste de {Poste}.</p>"
     "<p>Article 1 — Objet du contrat : {Description}.</p>"
     "<p>Article 2 — Durée : {Durée}.</p>"
     "<p>Article 3 — Rémunération : {Montant}.</p>"
     "<p>Fait à {Ville}, le {Date}, en deux exemplaires.</p>"),
    ("RAPPORT", "Rapport administratif", "LNFCL — Rapport",
     '<h2 style="text-align: center">RAPPORT</h2>'
     "<p><strong>Période :</strong> {Période}</p>"
     "<h3>1. Constats</h3><p>{Constats}</p>"
     "<h3>2. Activités réalisées</h3><ul><li>{Activité 1}</li><li>{Activité 2}</li></ul>"
     "<h3>3. Recommandations</h3><p>{Recommandations}</p>"),
    ("PV", "Procès-verbal de réunion", "LNFCL — Procès-verbal",
     '<h2 style="text-align: center">PROCÈS-VERBAL DE RÉUNION</h2>'
     "<p><strong>Date :</strong> {Date} — <strong>Lieu :</strong> {Lieu}</p>"
     "<p><strong>Participants :</strong> {Participants}</p>"
     "<h3>Ordre du jour</h3><ul><li>{Point 1}</li><li>{Point 2}</li></ul>"
     "<h3>Décisions</h3><p>{Décisions}</p>"),
    ("LISTE", "Liste des élèves", "LNFCL — Liste de classe",
     '<h2 style="text-align: center">LISTE DES ÉLÈVES — {Classe}</h2>'
     "<p>Année scolaire : {Année}</p>"
     "<table><tr><th>N°</th><th>Matricule</th><th>Nom complet</th><th>Sexe</th></tr>"
     "<tr><td>1</td><td>{Matricule}</td><td>{Nom}</td><td>{Sexe}</td></tr>"
     "<tr><td>2</td><td>{Matricule}</td><td>{Nom}</td><td>{Sexe}</td></tr></table>"),
    ("RECU", "Reçu de paiement", "LNFCL — Reçu",
     '<h2 style="text-align: center">REÇU DE PAIEMENT</h2>'
     "<p>Reçu de : <strong>{Nom du parent / élève}</strong></p>"
     "<p>La somme de : <strong>{Montant} HTG</strong></p>"
     "<p>Pour : {Motif} — Classe : {Classe}</p>"
     "<p>Mode de paiement : {Mode} — Reçu n° {Numéro}</p>"
     "<p>Date : {Date}</p>"
     '<p style="text-align: right"><strong>Signature</strong></p>'),
]


class Command(BaseCommand):
    help = "Crée les modèles de documents du Word Center."

    def handle(self, *args, **options):
        for category, name, header, body in TEMPLATES:
            DocumentTemplate.objects.get_or_create(
                name=name, category=category,
                defaults={"header_text": header, "body_html": body},
            )
        self.stdout.write(self.style.SUCCESS(f"{len(TEMPLATES)} modèles de documents prêts."))
