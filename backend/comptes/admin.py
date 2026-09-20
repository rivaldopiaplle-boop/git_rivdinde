"""Enregistrement dans le back-office technique (D-32).

Ce n'est pas l'interface du produit : c'est l'outil qui permet de corriger une
donnee ou de valider un compte avant que l'ecran Vue correspondant existe.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Administrateur, Adresse, Client, Gestionnaire, Livreur, Utilisateur, Vendeur


@admin.register(Utilisateur)
class UtilisateurAdmin(UserAdmin):
    ordering = ["-date_inscription"]
    list_display = ["email", "prenom", "nom", "role", "statut_compte", "date_inscription"]
    list_filter = ["role", "statut_compte"]
    search_fields = ["email", "nom", "prenom"]
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Identite", {"fields": ("prenom", "nom", "telephone")}),
        ("Role", {"fields": ("role", "statut_compte")}),
        ("Droits techniques", {"fields": ("is_staff", "is_superuser", "groups")}),
        ("Dates", {"fields": ("last_login",)}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "prenom", "nom", "role", "password1", "password2"),
        }),
    )


@admin.register(Vendeur)
class VendeurAdmin(admin.ModelAdmin):
    list_display = ["nom_boutique", "type_activite", "statut_validation", "utilisateur"]
    list_filter = ["type_activite", "statut_validation"]
    search_fields = ["nom_boutique"]


@admin.register(Livreur)
class LivreurAdmin(admin.ModelAdmin):
    list_display = ["utilisateur", "mode_livraison", "vehicule", "statut_validation",
                    "statut_disponibilite"]
    list_filter = ["mode_livraison", "statut_validation", "statut_disponibilite"]


admin.site.register([Client, Gestionnaire, Administrateur, Adresse])

admin.site.site_header = "RivDinde — back-office technique"
admin.site.site_title = "RivDinde"
admin.site.index_title = "Donnees de la plateforme"
