"""Ce que le catalogue expose, et sous quelle forme.

Deux serializers pour le produit, volontairement : la grille du catalogue
n'a pas besoin de la description ni de toutes les photos. Envoyer cinquante
fiches completes pour afficher cinquante vignettes est la premiere cause de
lenteur d'un catalogue.
"""
from rest_framework import serializers

from .models import Categorie, MouvementStock, PhotoProduit, Produit


def url_absolue(chemin, requete):
    """Une image peut etre un chemin local (developpement) ou une URL complete
    (Cloudinary en ligne). Le front ne doit pas avoir a faire la difference."""
    if not chemin:
        return ""
    if chemin.startswith("http"):
        return chemin
    return requete.build_absolute_uri(chemin) if requete else chemin


class CategorieSerializer(serializers.ModelSerializer):
    nombre_produits = serializers.IntegerField(read_only=True, required=False)

    class Meta:
        model = Categorie
        fields = ["id", "nom", "slug", "description", "nombre_produits"]


class PhotoProduitSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model = PhotoProduit
        fields = ["id", "url", "ordre", "texte_alternatif"]

    def get_url(self, photo):
        return url_absolue(photo.url, self.context.get("request"))


class _ProduitBase(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    boutique = serializers.SerializerMethodField()
    prix_centimes = serializers.IntegerField(source="prix_unitaire_centimes", read_only=True)
    disponible = serializers.SerializerMethodField()
    distance_km = serializers.SerializerMethodField()

    def get_image(self, produit):
        return url_absolue(produit.image_principale_url, self.context.get("request"))

    def get_boutique(self, produit):
        vendeur = produit.vendeur
        return {
            "id": vendeur.id,
            "nom": vendeur.nom_boutique,
            "type_service": vendeur.type_activite,
            "ville": vendeur.adresse.ville if vendeur.adresse else "",
        }

    def get_disponible(self, produit):
        # Le stock commandable, pas le stock brut : ce qui est reserve par un
        # paiement en cours n'est plus disponible (D-15).
        return produit.stock_commandable > 0

    def get_distance_km(self, produit):
        return self.context.get("distances", {}).get(produit.id)


class ProduitListeSerializer(_ProduitBase):
    """La vignette du catalogue : le strict necessaire pour une carte."""

    class Meta:
        model = Produit
        fields = ["id", "nom", "prix_centimes", "image", "boutique", "disponible", "distance_km"]


class ProduitDetailSerializer(_ProduitBase):
    photos = PhotoProduitSerializer(many=True, read_only=True)
    categorie = CategorieSerializer(read_only=True)

    class Meta:
        model = Produit
        fields = [
            "id", "nom", "description", "prix_centimes", "image", "photos",
            "boutique", "categorie", "disponible", "stock_disponible",
            "poids_grammes", "distance_km", "date_ajout",
        ]


class ProduitEcritureSerializer(serializers.ModelSerializer):
    """Ce qu'un vendeur peut ecrire. Le vendeur lui-meme vient du jeton, jamais
    de la charge utile : sinon on publierait dans la boutique d'un autre."""

    class Meta:
        model = Produit
        fields = [
            "id", "nom", "description", "prix_unitaire_centimes", "categorie",
            "poids_grammes", "stock_disponible", "seuil_alerte", "est_visible",
            "image_principale_url",
        ]

    def validate_prix_unitaire_centimes(self, valeur):
        if valeur < 1:
            raise serializers.ValidationError("Le prix doit etre d'au moins un centime.")
        return valeur


class BoutiqueSerializer(serializers.Serializer):
    """La boutique vue du catalogue public : ni chiffre d'affaires, ni SIRET,
    ni compte Stripe. Ce qui n'est pas necessaire ne sort pas."""

    id = serializers.IntegerField()
    nom = serializers.CharField(source="nom_boutique")
    type_service = serializers.CharField(source="type_activite")
    description = serializers.CharField()
    logo_url = serializers.CharField()
    note_moyenne = serializers.DecimalField(max_digits=3, decimal_places=2)
    ville = serializers.SerializerMethodField()
    nombre_produits = serializers.SerializerMethodField()
    distance_km = serializers.SerializerMethodField()

    def get_ville(self, vendeur):
        return vendeur.adresse.ville if vendeur.adresse else ""

    def get_nombre_produits(self, vendeur):
        return getattr(vendeur, "nombre_produits", None)

    def get_distance_km(self, vendeur):
        return self.context.get("distances", {}).get(vendeur.id)


class MouvementStockSerializer(serializers.ModelSerializer):
    auteur = serializers.SerializerMethodField()
    libelle_type = serializers.CharField(source="get_type_display", read_only=True)

    class Meta:
        model = MouvementStock
        fields = [
            "id", "type", "libelle_type", "quantite", "motif",
            "stock_apres", "date_mouvement", "auteur",
        ]

    def get_auteur(self, mouvement):
        # Qui a fait quoi : sans cette trace, un ecart de stock n'a plus
        # d'explication le lendemain.
        return str(mouvement.auteur) if mouvement.auteur else "—"
