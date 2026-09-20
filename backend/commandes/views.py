"""Le panier : accessible sans compte, conserve d'une visite a l'autre."""
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from catalogue.models import Produit
from comptes.models import StatutValidation

from .models import LignePanier
from .services import panier_courant, resume

# Le visiteur anonyme est identifie par une cle qu'il engendre lui-meme et
# garde dans son navigateur. Ce n'est pas un secret : elle ne donne acces qu'a
# un panier, et elle disparait a la fusion avec un compte.
ENTETE_SESSION = "HTTP_X_PANIER_SESSION"


def _cle(requete):
    return requete.META.get(ENTETE_SESSION, "")[:64]


@api_view(["GET"])
@permission_classes([AllowAny])
def voir_panier(requete):
    panier = panier_courant(requete.user, _cle(requete), creer=False)
    return Response({"data": resume(panier, requete)})


@api_view(["POST"])
@permission_classes([AllowAny])
def ajouter_ligne(requete):
    cle = _cle(requete)
    if not requete.user.is_authenticated and not cle:
        return Response(
            {"erreur": {"code": "session_absente",
                        "message": "Aucune session de panier fournie.", "details": {}}},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        produit = Produit.objects.select_related("vendeur").get(
            pk=requete.data.get("produit"),
            est_visible=True,
            vendeur__statut_validation=StatutValidation.VALIDE,
        )
    except Produit.DoesNotExist:
        return Response(
            {"erreur": {"code": "introuvable", "message": "Ce produit n'est plus disponible.",
                        "details": {}}},
            status=status.HTTP_404_NOT_FOUND,
        )

    quantite = max(1, int(requete.data.get("quantite", 1)))
    if produit.stock_commandable < quantite:
        return Response(
            {"erreur": {"code": "stock_insuffisant",
                        "message": f"Il ne reste que {produit.stock_commandable} exemplaire(s).",
                        "details": {}}},
            status=status.HTTP_409_CONFLICT,
        )

    panier = panier_courant(requete.user, cle)
    ligne = panier.lignes.filter(produit=produit).first()
    if ligne:
        ligne.quantite += quantite
        ligne.save(update_fields=["quantite"])
    else:
        LignePanier.objects.create(
            panier=panier, produit=produit, quantite=quantite,
            prix_capture_centimes=produit.prix_unitaire_centimes,
        )

    return Response({"data": resume(panier, requete)}, status=status.HTTP_201_CREATED)


@api_view(["PATCH", "DELETE"])
@permission_classes([AllowAny])
def modifier_ligne(requete, identifiant):
    panier = panier_courant(requete.user, _cle(requete), creer=False)
    if panier is None:
        return Response(status=status.HTTP_404_NOT_FOUND)

    ligne = get_object_or_404(LignePanier, pk=identifiant, panier=panier)

    if requete.method == "DELETE":
        ligne.delete()
        return Response({"data": resume(panier, requete)})

    quantite = int(requete.data.get("quantite", 1))
    if quantite < 1:
        ligne.delete()
    else:
        if ligne.produit.stock_commandable < quantite:
            return Response(
                {"erreur": {"code": "stock_insuffisant",
                            "message": f"Il ne reste que {ligne.produit.stock_commandable} "
                                       f"exemplaire(s).", "details": {}}},
                status=status.HTTP_409_CONFLICT,
            )
        ligne.quantite = quantite
        ligne.save(update_fields=["quantite"])

    return Response({"data": resume(panier, requete)})
