"""Les points d'entree HTTP de la zone comptes.

Equivalent des `*.controller.ts` de NestJS : ils recoivent, delegent, repondent.
Aucune regle metier n'est ecrite ici.
"""
from django.contrib.auth import authenticate
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Livreur, Role, StatutCompte, StatutValidation, Vendeur
from .permissions import EstAdmin, EstVendeur
from .serializers import (
    ConnexionSerializer,
    CreationGestionnaireSerializer,
    InscriptionClientSerializer,
    InscriptionLivreurSerializer,
    InscriptionVendeurSerializer,
    LivreurSerializer,
    MoiSerializer,
    UtilisateurSerializer,
    VendeurSerializer,
)


def _jetons(utilisateur):
    rafraichissement = RefreshToken.for_user(utilisateur)
    return {
        "acces": str(rafraichissement.access_token),
        "rafraichissement": str(rafraichissement),
    }


def _reponse_identite(utilisateur, code=status.HTTP_200_OK):
    donnees = MoiSerializer({"utilisateur": utilisateur}).data
    donnees.update(_jetons(utilisateur))
    return Response({"data": donnees}, status=code)


def _inscrire(requete, classe_serializer):
    serializer = classe_serializer(data=requete.data)
    serializer.is_valid(raise_exception=True)
    utilisateur = serializer.save()
    return _reponse_identite(utilisateur, status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([AllowAny])
def inscription_client(requete):
    return _inscrire(requete, InscriptionClientSerializer)


@api_view(["POST"])
@permission_classes([AllowAny])
def inscription_vendeur(requete):
    return _inscrire(requete, InscriptionVendeurSerializer)


@api_view(["POST"])
@permission_classes([AllowAny])
def inscription_livreur(requete):
    return _inscrire(requete, InscriptionLivreurSerializer)


@api_view(["POST"])
@permission_classes([AllowAny])
def connexion(requete):
    serializer = ConnexionSerializer(data=requete.data)
    serializer.is_valid(raise_exception=True)

    utilisateur = authenticate(
        requete,
        username=serializer.validated_data["email"].lower(),
        password=serializer.validated_data["mot_de_passe"],
    )
    if utilisateur is None:
        # Un seul message pour « e-mail inconnu » et « mot de passe faux » :
        # les distinguer permettrait d'enumerer les comptes existants.
        return Response(
            {"erreur": {"code": "identifiants", "message": "E-mail ou mot de passe incorrect.",
                        "details": {}}},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    if not utilisateur.peut_se_connecter:
        return Response(
            {"erreur": {"code": "compte_bloque",
                        "message": "Ce compte a ete suspendu ou desactive.", "details": {}}},
            status=status.HTTP_403_FORBIDDEN,
        )

    utilisateur.last_login = timezone.now()
    utilisateur.save(update_fields=["last_login"])

    _fusionner_panier(requete, utilisateur)
    return _reponse_identite(utilisateur)


def _fusionner_panier(requete, utilisateur):
    """Le panier rempli avant la connexion suit le client (D-03).

    Sans cela, un visiteur qui remplit son panier puis se connecte le retrouve
    vide — et il ne revient pas.
    """
    cle = requete.META.get("HTTP_X_PANIER_SESSION", "")[:64]
    if not cle or not hasattr(utilisateur, "profil_client"):
        return

    from commandes.services import fusionner, panier_courant

    invite = panier_courant(AnonymeAvecCle(), cle, creer=False)
    if invite is None:
        return
    fusionner(invite, panier_courant(utilisateur, "", creer=True))


class AnonymeAvecCle:
    """Un faux visiteur anonyme, pour reutiliser `panier_courant` tel quel."""

    is_authenticated = False


@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
def moi(requete):
    if requete.method == "PATCH":
        serializer = UtilisateurSerializer(requete.user, data=requete.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
    return Response({"data": MoiSerializer({"utilisateur": requete.user}).data})


@api_view(["POST"])
@permission_classes([EstVendeur])
def creer_gestionnaire(requete):
    """Un vendeur cree son propre personnel, et seulement le sien (D-04)."""
    profil = getattr(requete.user, "profil_vendeur", None)
    if profil is None:
        return Response(
            {"erreur": {"code": "profil_absent", "message": "Aucune boutique rattachee.",
                        "details": {}}},
            status=status.HTTP_400_BAD_REQUEST,
        )
    donnees = dict(requete.data)
    donnees["type_gestionnaire"] = "STAFF_VENDEUR"
    serializer = CreationGestionnaireSerializer(data=donnees, context={"vendeur": profil})
    serializer.is_valid(raise_exception=True)
    utilisateur = serializer.save()
    return Response(
        {"data": UtilisateurSerializer(utilisateur).data}, status=status.HTTP_201_CREATED
    )


@api_view(["GET"])
@permission_classes([EstAdmin])
def validations_en_attente(requete):
    """Le tableau de bord admin : qui attend une decision, et depuis quand."""
    vendeurs = Vendeur.objects.filter(statut_validation=StatutValidation.EN_ATTENTE)
    livreurs = Livreur.objects.filter(statut_validation=StatutValidation.EN_ATTENTE)
    return Response({"data": {
        "vendeurs": VendeurSerializer(vendeurs, many=True).data,
        "livreurs": LivreurSerializer(livreurs, many=True).data,
    }})


def _decider(modele, serializer_classe, identifiant, valide, motif=""):
    try:
        profil = modele.objects.select_related("utilisateur").get(pk=identifiant)
    except modele.DoesNotExist:
        return None

    profil.statut_validation = StatutValidation.VALIDE if valide else StatutValidation.REJETE
    profil.save(update_fields=["statut_validation"])

    # Le compte passe actif seulement si la decision est positive : un rejet
    # laisse le compte en attente, il n'ouvre pas l'acces (R-07).
    utilisateur = profil.utilisateur
    utilisateur.statut_compte = (
        StatutCompte.ACTIF if valide else StatutCompte.EN_ATTENTE
    )
    utilisateur.save(update_fields=["statut_compte"])
    return serializer_classe(profil).data


@api_view(["POST"])
@permission_classes([EstAdmin])
def valider_vendeur(requete, identifiant):
    donnees = _decider(Vendeur, VendeurSerializer, identifiant, valide=True)
    if donnees is None:
        return Response(status=status.HTTP_404_NOT_FOUND)
    return Response({"data": donnees})


@api_view(["POST"])
@permission_classes([EstAdmin])
def rejeter_vendeur(requete, identifiant):
    donnees = _decider(Vendeur, VendeurSerializer, identifiant, valide=False)
    if donnees is None:
        return Response(status=status.HTTP_404_NOT_FOUND)
    return Response({"data": donnees})


@api_view(["POST"])
@permission_classes([EstAdmin])
def valider_livreur(requete, identifiant):
    donnees = _decider(Livreur, LivreurSerializer, identifiant, valide=True)
    if donnees is None:
        return Response(status=status.HTTP_404_NOT_FOUND)
    return Response({"data": donnees})


@api_view(["GET"])
@permission_classes([EstAdmin])
def tableau_de_bord_admin(requete):
    from django.contrib.auth import get_user_model

    Utilisateur = get_user_model()
    return Response({"data": {
        "utilisateurs": Utilisateur.objects.count(),
        "vendeurs_en_attente": Vendeur.objects.filter(
            statut_validation=StatutValidation.EN_ATTENTE).count(),
        "livreurs_en_attente": Livreur.objects.filter(
            statut_validation=StatutValidation.EN_ATTENTE).count(),
        "clients": Utilisateur.objects.filter(role=Role.CLIENT).count(),
    }})
