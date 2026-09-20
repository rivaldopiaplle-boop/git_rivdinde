"""Une classe de permission par ligne de la matrice des droits.

Equivalent direct des `guards/` de NestJS. La regle qui les gouverne toutes :
**l'autorisation se verifie cote serveur**, jamais en cachant un bouton. Un
role qui appelle l'URL d'un autre role recoit 403 (scenarios 14.1 et 14.2).
"""
from rest_framework.permissions import BasePermission

from .models import Role, StatutCompte, StatutValidation


class EstActif(BasePermission):
    """Un compte suspendu garde ses jetons mais ne peut plus rien faire."""

    message = "Ce compte n'est pas actif."

    def has_permission(self, requete, vue):
        utilisateur = requete.user
        return bool(
            utilisateur
            and utilisateur.is_authenticated
            and utilisateur.statut_compte == StatutCompte.ACTIF
        )


class _RoleRequis(BasePermission):
    role = None

    def has_permission(self, requete, vue):
        utilisateur = requete.user
        return bool(
            utilisateur
            and utilisateur.is_authenticated
            and utilisateur.role == self.role
            and utilisateur.statut_compte == StatutCompte.ACTIF
        )


class EstClient(_RoleRequis):
    role = Role.CLIENT
    message = "Reserve aux clients."


class EstVendeur(_RoleRequis):
    role = Role.VENDEUR
    message = "Reserve aux vendeurs."


class EstGestionnaire(_RoleRequis):
    role = Role.GESTIONNAIRE
    message = "Reserve au personnel."


class EstLivreur(_RoleRequis):
    role = Role.LIVREUR
    message = "Reserve aux livreurs."


class EstAdmin(_RoleRequis):
    role = Role.ADMIN
    message = "Reserve aux administrateurs."


class EstVendeurValide(EstVendeur):
    """Un vendeur en attente se connecte, mais ne publie rien (R-07)."""

    message = "Votre boutique n'est pas encore validee."

    def has_permission(self, requete, vue):
        if not super().has_permission(requete, vue):
            return False
        profil = getattr(requete.user, "profil_vendeur", None)
        return bool(profil and profil.statut_validation == StatutValidation.VALIDE)


class EstLivreurValide(EstLivreur):
    message = "Votre compte livreur n'est pas encore valide."

    def has_permission(self, requete, vue):
        if not super().has_permission(requete, vue):
            return False
        profil = getattr(requete.user, "profil_livreur", None)
        return bool(profil and profil.statut_validation == StatutValidation.VALIDE)


class EstVendeurOuSonPersonnel(BasePermission):
    """Le vendeur, ou un gestionnaire employe par un vendeur.

    Le stock est un travail d'atelier : le gestionnaire qui prepare les
    commandes constate les casses et les ecarts. Lui refuser l'ajustement
    obligerait a deranger le vendeur a chaque fois. Les prix et le chiffre
    d'affaires, eux, restent au vendeur seul (D-04).
    """

    message = "Reserve au vendeur et a son personnel."

    def has_permission(self, requete, vue):
        utilisateur = requete.user
        if not utilisateur or not utilisateur.is_authenticated:
            return False
        if utilisateur.statut_compte != StatutCompte.ACTIF:
            return False
        if utilisateur.role == Role.VENDEUR:
            return True
        if utilisateur.role != Role.GESTIONNAIRE:
            return False
        profil = getattr(utilisateur, "profil_gestionnaire", None)
        return bool(profil and profil.vendeur_id)
