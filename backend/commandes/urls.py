from django.urls import path

from . import views, vues_commande

urlpatterns = [
    path("panier", views.voir_panier, name="voir-panier"),
    path("panier/lignes", views.ajouter_ligne, name="ajouter-ligne"),
    path("panier/lignes/<int:identifiant>", views.modifier_ligne, name="modifier-ligne"),
    path("panier/apercu-commandes", vues_commande.apercu_commandes, name="apercu-commandes"),

    path("commandes", vues_commande.creer_commandes, name="creer-commandes"),
    path("mes-commandes", vues_commande.mes_commandes, name="mes-commandes"),
    path("commandes/<int:identifiant>", vues_commande.detail_commande, name="detail-commande"),

    path("vendeurs/commandes", vues_commande.commandes_recues, name="commandes-recues"),
    path("vendeurs/sous-commandes/<int:identifiant>", vues_commande.avancer_preparation,
         name="avancer-preparation"),
]
