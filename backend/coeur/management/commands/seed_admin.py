"""Cree le tout premier compte administrateur — decision D-01.

Il n'existe et il n'existera jamais de formulaire public « devenir admin » :
ce serait la faille la plus evidente du projet. Le compte fondateur est donc
cree par cette commande, executee une fois, hors de toute interface web. Les
admins suivants seront crees par un admin depuis le back-office.

    python manage.py seed_admin

La commande est **idempotente** : la rejouer ne cree pas de doublon et ne
casse rien. Elle remet simplement le compte en etat (actif, superutilisateur)
et, si un mot de passe est fourni, le reapplique.
"""
import os
import secrets
import string

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from comptes.models import Administrateur, Role, StatutCompte


def mot_de_passe_lisible(longueur=16):
    """Un mot de passe fort mais recopiable a la main, sans caractere ambigu.

    Ni l ni I ni 1, ni O ni 0 : un mot de passe qu'on n'arrive pas a relire
    depuis un terminal finit colle dans un fichier, ou pire, simplifie.
    """
    alphabet = (
        "".join(c for c in string.ascii_letters if c not in "lIO")
        + "".join(c for c in string.digits if c not in "01")
        + "!@#%*-_"
    )
    return "".join(secrets.choice(alphabet) for _ in range(longueur))


class Command(BaseCommand):
    help = "Cree ou remet en etat le compte administrateur fondateur."

    def add_arguments(self, analyseur):
        analyseur.add_argument(
            "--mot-de-passe",
            dest="mot_de_passe",
            default=None,
            help="Impose un mot de passe. Sinon : ADMIN_MOT_DE_PASSE, ou un mot "
                 "de passe engendre et affiche une seule fois.",
        )

    def handle(self, *args, **options):
        Utilisateur = get_user_model()

        email = os.environ.get("ADMIN_EMAIL", "").strip() or "admin@rivdinde.local"
        mot_de_passe = (
            options["mot_de_passe"]
            or os.environ.get("ADMIN_MOT_DE_PASSE", "").strip()
        )
        engendre = False
        existe_deja = Utilisateur.objects.filter(email=email).exists()

        # Un mot de passe engendre a chaque appel changerait celui de l'admin
        # a chaque `demarrer.py` : on n'en engendre un que pour un compte
        # nouveau. Un compte deja en place garde le sien.
        if not mot_de_passe and existe_deja:
            compte = Utilisateur.objects.get(email=email)
            compte.role = Role.ADMIN
            compte.statut_compte = StatutCompte.ACTIF
            compte.is_staff = True
            compte.is_superuser = True
            compte.is_active = True
            compte.save()
            self.stdout.write("")
            self.stdout.write(self.style.SUCCESS("Compte administrateur deja en place."))
            self.stdout.write(f"  Adresse    : {email}")
            self.stdout.write("  Mot de passe : inchange")
            self.stdout.write("  Connexion  : http://localhost:8000/admin/")
            self.stdout.write("")
            return

        if not mot_de_passe:
            # Hors developpement, engendrer un mot de passe et l'afficher dans
            # les journaux de l'hebergeur serait pire que de refuser.
            if not settings.DEBUG:
                raise CommandError(
                    "ADMIN_MOT_DE_PASSE est obligatoire hors developpement. "
                    "Renseigne-le dans l'environnement, puis relance."
                )
            mot_de_passe = mot_de_passe_lisible()
            engendre = True

        compte, cree = Utilisateur.objects.get_or_create(
            email=email,
            defaults={"nom": "Plateforme", "prenom": "Admin", "role": Role.ADMIN},
        )
        compte.role = Role.ADMIN
        compte.statut_compte = StatutCompte.ACTIF
        compte.is_staff = True
        compte.is_superuser = True
        compte.is_active = True
        compte.set_password(mot_de_passe)
        compte.save()

        # Le profil metier, sans lequel l'admin n'existe que techniquement.
        Administrateur.objects.get_or_create(
            utilisateur=compte, defaults={"niveau": "SUPER_ADMIN"}
        )

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(
            f"Compte administrateur {'cree' if cree else 'remis en etat'}."
        ))
        self.stdout.write(f"  Adresse    : {email}")

        if engendre:
            # Affiche une seule fois, et seulement quand c'est nous qui l'avons
            # engendre : un mot de passe venu de l'environnement n'a aucune
            # raison de reapparaitre dans un terminal.
            self.stdout.write(f"  Mot de passe : {self.style.WARNING(mot_de_passe)}")
            self.stdout.write("")
            self.stdout.write(
                "  Note-le : il ne sera pas reaffiche. Pour en fixer un a toi,\n"
                "  renseigne ADMIN_MOT_DE_PASSE dans backend/.env puis relance\n"
                "  cette commande."
            )
        else:
            self.stdout.write("  Mot de passe : celui d'ADMIN_MOT_DE_PASSE (non affiche)")

        self.stdout.write("")
        self.stdout.write("  Connexion  : http://localhost:8000/admin/")
        self.stdout.write("")
