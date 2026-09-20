from django.contrib import admin

from .models import AlerteDisponibilite, Categorie, MouvementStock, PhotoProduit, Produit


class PhotoEnLigne(admin.TabularInline):
    model = PhotoProduit
    extra = 0


@admin.register(Produit)
class ProduitAdmin(admin.ModelAdmin):
    list_display = ["nom", "vendeur", "prix_unitaire_centimes", "stock_disponible", "est_visible"]
    list_filter = ["est_visible", "vendeur__type_activite", "categorie"]
    search_fields = ["nom", "description"]
    inlines = [PhotoEnLigne]


@admin.register(Categorie)
class CategorieAdmin(admin.ModelAdmin):
    list_display = ["nom", "slug", "parente"]
    prepopulated_fields = {"slug": ["nom"]}


admin.site.register([MouvementStock, AlerteDisponibilite])
