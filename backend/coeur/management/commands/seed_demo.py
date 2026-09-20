"""Peuple une base vide avec les personae du dossier de conception.

    python manage.py seed_demo

Les noms ne sont pas choisis au hasard : ce sont ceux de
plan-organisation/01-produit/scenarios.md. Quand un scenario parle de « Lea
commande chez Karim », on peut le derouler tel quel a l'ecran.

La commande est **idempotente** : la rejouer ne cree pas de doublon. Elle ne
touche jamais a un compte existant, ce qui permet de la lancer a chaque
demarrage sans reflechir.

Le mot de passe de demonstration est volontairement le meme pour tous et ecrit
en clair ici : c'est un jeu de donnees de vitrine, pas des comptes reels. Il
n'est cree que si DEBUG est actif ou si DEMO_AUTORISEE est mise.
"""
import os

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from comptes.models import (
    Adresse,
    Client,
    Gestionnaire,
    Livreur,
    Role,
    StatutCompte,
    StatutValidation,
    TypeGestionnaire,
    TypeService,
    Utilisateur,
    Vendeur,
)
from livraisons.models import Entrepot, ZoneLivraison

MOT_DE_PASSE_DEMO = "Demonstration!2026"


class Command(BaseCommand):
    help = "Cree les comptes et les lieux de demonstration."

    @transaction.atomic
    def handle(self, *args, **options):
        if not settings.DEBUG and not os.environ.get("DEMO_AUTORISEE"):
            raise CommandError(
                "seed_demo cree des comptes a mot de passe connu. "
                "Hors developpement, il faut poser DEMO_AUTORISEE=1 sciemment."
            )

        cree = []

        def utilisateur(email, prenom, nom, role, statut=StatutCompte.ACTIF):
            existant = Utilisateur.objects.filter(email=email).first()
            if existant:
                return existant, False
            compte = Utilisateur.objects.create_user(
                email=email, password=MOT_DE_PASSE_DEMO, prenom=prenom, nom=nom,
                role=role, statut_compte=statut,
            )
            cree.append(email)
            return compte, True

        # ── Les lieux ────────────────────────────────────────────────────
        adresse_entrepot, _ = Adresse.objects.get_or_create(
            rue="12 rue de la Logistique", code_postal="69100", ville="Villeurbanne",
            defaults={"libelle": "Entrepot Est", "latitude": 45.7719, "longitude": 4.8902},
        )
        entrepot, _ = Entrepot.objects.get_or_create(
            nom="Entrepot Lyon-Est",
            defaults={"adresse": adresse_entrepot, "capacite": 5000},
        )
        zone, _ = ZoneLivraison.objects.get_or_create(
            nom="Lyon et couronne",
            defaults={
                "codes_postaux": "69001,69002,69003,69006,69007,69100",
                "entrepot": entrepot,
                "frais_base_centimes": 490,
                "seuil_gratuite_centimes": 5000,
            },
        )

        # ── Lea, cliente ─────────────────────────────────────────────────
        compte_lea, neuf = utilisateur("lea@exemple.fr", "Lea", "Martin", Role.CLIENT)
        client_lea, _ = Client.objects.get_or_create(utilisateur=compte_lea)
        adresse_lea, _ = Adresse.objects.get_or_create(
            rue="8 rue Victor Hugo", code_postal="69002", ville="Lyon",
            defaults={
                "libelle": "Domicile", "latitude": 45.7550, "longitude": 4.8320,
                "zone": zone, "instructions_livraison": "Code portail 4512, 3e etage.",
            },
        )
        client_lea.adresses.through.objects.get_or_create(
            client=client_lea, adresse=adresse_lea, defaults={"est_principale": True}
        )

        # ── Karim, vendeur Express — et Nadia, son personnel ─────────────
        compte_karim, _ = utilisateur("karim@exemple.fr", "Karim", "Benali", Role.VENDEUR)
        adresse_karim, _ = Adresse.objects.get_or_create(
            rue="24 cours Gambetta", code_postal="69003", ville="Lyon",
            defaults={"libelle": "Chez Karim", "latitude": 45.7545, "longitude": 4.8480,
                      "zone": zone},
        )
        vendeur_karim, _ = Vendeur.objects.get_or_create(
            utilisateur=compte_karim,
            defaults={
                "nom_boutique": "Chez Karim", "type_activite": TypeService.EXPRESS,
                "adresse": adresse_karim, "rayon_livraison_km": 6,
                "statut_validation": StatutValidation.VALIDE,
                "description": "Cuisine du marche, prete en quinze minutes.",
            },
        )
        compte_nadia, _ = utilisateur("nadia@exemple.fr", "Nadia", "Sow", Role.GESTIONNAIRE)
        Gestionnaire.objects.get_or_create(
            utilisateur=compte_nadia,
            defaults={"type_gestionnaire": TypeGestionnaire.STAFF_VENDEUR,
                      "vendeur": vendeur_karim},
        )

        # ── Sophie, vendeuse Standard ────────────────────────────────────
        compte_sophie, _ = utilisateur("sophie@exemple.fr", "Sophie", "Leroy", Role.VENDEUR)
        adresse_sophie, _ = Adresse.objects.get_or_create(
            rue="5 avenue Jean Jaures", code_postal="69007", ville="Lyon",
            defaults={"libelle": "TechSophie", "latitude": 45.7420, "longitude": 4.8410,
                      "zone": zone},
        )
        Vendeur.objects.get_or_create(
            utilisateur=compte_sophie,
            defaults={
                "nom_boutique": "TechSophie", "type_activite": TypeService.STANDARD,
                "adresse": adresse_sophie,
                "statut_validation": StatutValidation.VALIDE,
                "description": "Electronique reconditionnee, garantie deux ans.",
            },
        )

        # ── Un vendeur qui attend, pour que l'ecran de validation ait
        #    quelque chose a montrer des le premier lancement ─────────────
        compte_ines, _ = utilisateur(
            "ines@exemple.fr", "Ines", "Haddad", Role.VENDEUR, StatutCompte.EN_ATTENTE
        )
        Vendeur.objects.get_or_create(
            utilisateur=compte_ines,
            defaults={"nom_boutique": "Fleurs d'Ines", "type_activite": TypeService.EXPRESS},
        )

        # ── Amine (Express) et Julien (Standard) ─────────────────────────
        compte_amine, _ = utilisateur("amine@exemple.fr", "Amine", "Cherif", Role.LIVREUR)
        Livreur.objects.get_or_create(
            utilisateur=compte_amine,
            defaults={"mode_livraison": TypeService.EXPRESS, "vehicule": "VELO",
                      "statut_validation": StatutValidation.VALIDE},
        )
        compte_julien, _ = utilisateur("julien@exemple.fr", "Julien", "Moreau", Role.LIVREUR)
        Livreur.objects.get_or_create(
            utilisateur=compte_julien,
            defaults={"mode_livraison": TypeService.STANDARD, "vehicule": "CAMIONNETTE",
                      "entrepot": entrepot, "statut_validation": StatutValidation.VALIDE},
        )

        # ── Rachid, gestionnaire d'entrepot ──────────────────────────────
        compte_rachid, _ = utilisateur("rachid@exemple.fr", "Rachid", "Amrani", Role.GESTIONNAIRE)
        Gestionnaire.objects.get_or_create(
            utilisateur=compte_rachid,
            defaults={"type_gestionnaire": TypeGestionnaire.STAFF_ENTREPOT, "entrepot": entrepot},
        )

        # Le catalogue vient juste apres les boutiques : une vitrine sans
        # produit ne prouve rien et ne se montre pas.
        call_command("seed_catalogue")

        self.stdout.write("")
        if cree:
            self.stdout.write(
                self.style.SUCCESS(f"Jeu de demonstration : {len(cree)} compte(s) cree(s).")
            )
        else:
            self.stdout.write(self.style.SUCCESS("Jeu de demonstration deja en place."))
        self.stdout.write(f"  Mot de passe commun : {self.style.WARNING(MOT_DE_PASSE_DEMO)}")
        self.stdout.write("")
        for email, qui in [
            ("lea@exemple.fr", "cliente"),
            ("karim@exemple.fr", "vendeur Express, valide"),
            ("sophie@exemple.fr", "vendeuse Standard, validee"),
            ("ines@exemple.fr", "vendeuse EN ATTENTE de validation"),
            ("nadia@exemple.fr", "gestionnaire, personnel de Karim"),
            ("rachid@exemple.fr", "gestionnaire d'entrepot"),
            ("amine@exemple.fr", "livreur Express"),
            ("julien@exemple.fr", "livreur Standard"),
        ]:
            self.stdout.write(f"  {email:<22} {qui}")
        self.stdout.write("")
