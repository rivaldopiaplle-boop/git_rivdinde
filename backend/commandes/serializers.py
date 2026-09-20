"""Le panier, tel que le front le consomme."""
from rest_framework import serializers

from catalogue.serializers import url_absolue

from .models import LignePanier


class LignePanierSerializer(serializers.ModelSerializer):
    produit = serializers.SerializerMethodField()
    sous_total_centimes = serializers.SerializerMethodField()
    prix_a_change = serializers.SerializerMethodField()

    class Meta:
        model = LignePanier
        fields = [
            "id", "quantite", "prix_capture_centimes", "sous_total_centimes",
            "prix_a_change", "produit",
        ]

    def get_produit(self, ligne):
        produit = ligne.produit
        return {
            "id": produit.id,
            "nom": produit.nom,
            "prix_centimes": produit.prix_unitaire_centimes,
            "image": url_absolue(produit.image_principale_url, self.context.get("request")),
            "stock_commandable": produit.stock_commandable,
            "boutique": {
                "id": produit.vendeur_id,
                "nom": produit.vendeur.nom_boutique,
                "type_service": produit.vendeur.type_activite,
            },
        }

    def get_sous_total_centimes(self, ligne):
        # Le prix qui compte est le prix COURANT, jamais celui capture a
        # l'ajout : le panier affiche ce que le client paiera (R-05).
        return ligne.produit.prix_unitaire_centimes * ligne.quantite

    def get_prix_a_change(self, ligne):
        return ligne.produit.prix_unitaire_centimes != ligne.prix_capture_centimes
