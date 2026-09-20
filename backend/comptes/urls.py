"""Les chemins suivent 03-contrats/contrat-api.md, au caractere pres.

Un contrat qui n'est pas respecte par le code n'est plus un contrat.
"""
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from . import views

urlpatterns = [
    path("auth/inscription/client", views.inscription_client, name="inscription-client"),
    path("auth/inscription/vendeur", views.inscription_vendeur, name="inscription-vendeur"),
    path("auth/inscription/livreur", views.inscription_livreur, name="inscription-livreur"),
    path("auth/connexion", views.connexion, name="connexion"),
    path("auth/rafraichir", TokenRefreshView.as_view(), name="rafraichir"),

    path("moi", views.moi, name="moi"),

    path("vendeurs/gestionnaires", views.creer_gestionnaire, name="creer-gestionnaire"),

    path("admin/tableau-de-bord", views.tableau_de_bord_admin, name="tableau-de-bord-admin"),
    path("admin/validations", views.validations_en_attente, name="validations"),
    path("admin/vendeurs/<int:identifiant>/valider", views.valider_vendeur, name="valider-vendeur"),
    path("admin/vendeurs/<int:identifiant>/rejeter", views.rejeter_vendeur, name="rejeter-vendeur"),
    path("admin/livreurs/<int:identifiant>/valider", views.valider_livreur, name="valider-livreur"),
]
