"""La logique du panier, hors des vues.

Equivalent des `*.service.ts` de NestJS : les vues recoivent et repondent,
c'est ici que les regles vivent.
"""
from django.db import transaction

from .models import LignePanier, Panier, StatutPanier


def panier_courant(utilisateur, cle_session, creer=True):
    """Le panier actif : celui du compte s'il est connecte, sinon celui de la
    session anonyme. Le compte n'est exige qu'au paiement (D-03)."""
    profil = getattr(utilisateur, "profil_client", None) if utilisateur.is_authenticated else None

    if profil is not None:
        panier = Panier.objects.filter(client=profil, statut=StatutPanier.ACTIF).first()
        if panier is None and creer:
            panier = Panier.objects.create(client=profil)
        return panier

    if not cle_session:
        return None
    panier = Panier.objects.filter(cle_session=cle_session, statut=StatutPanier.ACTIF).first()
    if panier is None and creer:
        panier = Panier.objects.create(cle_session=cle_session)
    return panier


@transaction.atomic
def fusionner(panier_invite, panier_client):
    """Reunit le panier anonyme et celui du compte a la connexion (D-03).

    Sans cette fusion, un visiteur qui remplit son panier puis se connecte le
    retrouve vide — et il ne revient pas.
    """
    if panier_invite is None or panier_client is None or panier_invite.pk == panier_client.pk:
        return panier_client

    for ligne in panier_invite.lignes.select_related("produit"):
        existante = panier_client.lignes.filter(produit=ligne.produit).first()
        if existante:
            existante.quantite += ligne.quantite
            existante.save(update_fields=["quantite"])
        else:
            LignePanier.objects.create(
                panier=panier_client, produit=ligne.produit,
                quantite=ligne.quantite, prix_capture_centimes=ligne.prix_capture_centimes,
            )

    panier_invite.statut = StatutPanier.ABANDONNE
    panier_invite.save(update_fields=["statut"])
    return panier_client


def resume(panier, requete):
    """Ce que le front affiche dans son panneau lateral."""
    from .serializers import LignePanierSerializer

    if panier is None:
        return {"id": None, "lignes": [], "nombre_articles": 0, "total_centimes": 0,
                "boutiques": []}

    lignes = panier.lignes.select_related("produit", "produit__vendeur").all()
    donnees = LignePanierSerializer(lignes, many=True, context={"request": requete}).data
    boutiques = sorted({ligne["produit"]["boutique"]["nom"] for ligne in donnees})

    return {
        "id": panier.id,
        "lignes": donnees,
        "nombre_articles": sum(ligne["quantite"] for ligne in donnees),
        "total_centimes": sum(ligne["sous_total_centimes"] for ligne in donnees),
        # Un panier a plusieurs boutiques donnera plusieurs commandes (D-10) :
        # autant le montrer des le panier plutot qu'a la surprise du paiement.
        "boutiques": boutiques,
    }
