"""Ce que l'API expose d'une commande, selon qui regarde."""
from rest_framework import serializers

from catalogue.serializers import url_absolue

from .models import Commande, LigneCommande, SousCommande


class LigneCommandeSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = LigneCommande
        fields = [
            "id", "nom_produit_capture", "prix_unitaire_centimes",
            "quantite", "sous_total_centimes", "image",
        ]

    def get_image(self, ligne):
        produit = ligne.produit
        return url_absolue(produit.image_principale_url, self.context.get("request")) if produit else ""


class SousCommandeSerializer(serializers.ModelSerializer):
    boutique = serializers.CharField(source="vendeur.nom_boutique", read_only=True)
    lignes = LigneCommandeSerializer(many=True, read_only=True)
    libelle_statut = serializers.CharField(source="get_statut_preparation_display", read_only=True)

    class Meta:
        model = SousCommande
        fields = [
            "id", "boutique", "statut_preparation", "libelle_statut",
            "montant_vendeur_centimes", "montant_commission_centimes", "lignes",
        ]


class CommandeSerializer(serializers.ModelSerializer):
    sous_commandes = SousCommandeSerializer(many=True, read_only=True)
    libelle_statut = serializers.CharField(source="get_statut_actuel_display", read_only=True)
    adresse = serializers.SerializerMethodField()
    boutiques = serializers.SerializerMethodField()

    class Meta:
        model = Commande
        fields = [
            "id", "numero_commande", "type_service", "statut_actuel", "libelle_statut",
            "montant_produits_centimes", "montant_livraison_centimes",
            "montant_total_centimes", "date_commande", "date_livraison_estimee",
            "adresse", "boutiques", "sous_commandes",
        ]

    def get_adresse(self, commande):
        adresse = commande.adresse_livraison
        return f"{adresse.rue}, {adresse.code_postal} {adresse.ville}"

    def get_boutiques(self, commande):
        return [sous.vendeur.nom_boutique for sous in commande.sous_commandes.all()]
