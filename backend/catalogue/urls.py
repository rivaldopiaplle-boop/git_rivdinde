from django.urls import path

from . import views

urlpatterns = [
    path("produits", views.liste_produits, name="liste-produits"),
    path("produits/<int:identifiant>", views.detail_produit, name="detail-produit"),
    path("categories", views.liste_categories, name="liste-categories"),
    path("boutiques", views.liste_boutiques, name="liste-boutiques"),

    path("vendeurs/produits", views.mes_produits, name="mes-produits"),
    path("vendeurs/produits/<int:identifiant>", views.modifier_produit, name="modifier-produit"),
    path("vendeurs/stock-bas", views.stock_bas, name="stock-bas"),

    # Photos — contrat-medias.md § 6
    path("produits/<int:identifiant>/photos", views.televerser_photos, name="televerser-photos"),
    path("produits/<int:identifiant>/photos/ordre", views.ordonner_photos, name="ordonner-photos"),
    path("produits/<int:identifiant>/photos/<int:id_photo>", views.retirer_photo,
         name="retirer-photo"),

    # Stock — scenario 4.4
    path("produits/<int:identifiant>/stock", views.modifier_stock, name="modifier-stock"),
    path("produits/<int:identifiant>/mouvements", views.mouvements_du_produit,
         name="mouvements-produit"),
]
