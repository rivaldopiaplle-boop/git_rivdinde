from django.contrib import admin

from .models import Commande, HistoriqueStatut, LigneCommande, LignePanier, Panier, SousCommande


class LignePanierEnLigne(admin.TabularInline):
    model = LignePanier
    extra = 0


@admin.register(Panier)
class PanierAdmin(admin.ModelAdmin):
    list_display = ["id", "client", "statut", "date_maj"]
    list_filter = ["statut"]
    inlines = [LignePanierEnLigne]


@admin.register(Commande)
class CommandeAdmin(admin.ModelAdmin):
    list_display = ["numero_commande", "client", "type_service", "statut_actuel",
                    "montant_total_centimes", "date_commande"]
    list_filter = ["type_service", "statut_actuel"]
    search_fields = ["numero_commande"]


admin.site.register([SousCommande, LigneCommande, HistoriqueStatut])
