"""Zone 4 du modele — paiement, repartition, facturation, promotions."""
from django.db import models


class StatutPaiement(models.TextChoices):
    EN_ATTENTE = "EN_ATTENTE", "En attente"
    AUTORISE = "AUTORISE", "Autorise"
    CAPTURE = "CAPTURE", "Capture"
    ECHOUE = "ECHOUE", "Echoue"
    REMBOURSE = "REMBOURSE", "Rembourse"


class Paiement(models.Model):
    """La confirmation vient du webhook serveur-a-serveur, jamais du retour
    navigateur (D-12) : un client qui ferme son onglet ne doit pas empecher
    une commande payee d'etre reconnue comme telle."""

    commande = models.OneToOneField(
        "commandes.Commande", on_delete=models.PROTECT, related_name="paiement"
    )
    montant_centimes = models.PositiveIntegerField()
    methode = models.CharField(max_length=30, default="CARTE")
    statut_paiement = models.CharField(
        max_length=12, choices=StatutPaiement.choices, default=StatutPaiement.EN_ATTENTE
    )
    reference_stripe = models.CharField(max_length=120, blank=True, db_index=True)
    date_paiement = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.montant_centimes / 100:.2f} EUR ({self.get_statut_paiement_display()})"


class RepartitionVendeur(models.Model):
    """Ce que Stripe Connect a reverse a qui. Sans cette trace, aucun audit
    n'est possible sur une commande multi-vendeur."""

    paiement = models.ForeignKey(Paiement, on_delete=models.CASCADE, related_name="repartitions")
    sous_commande = models.OneToOneField(
        "commandes.SousCommande", on_delete=models.CASCADE, related_name="repartition"
    )
    vendeur = models.ForeignKey(
        "comptes.Vendeur", on_delete=models.PROTECT, related_name="repartitions"
    )
    montant_vendeur_centimes = models.PositiveIntegerField()
    montant_commission_centimes = models.PositiveIntegerField()
    reference_transfert_stripe = models.CharField(max_length=120, blank=True)
    statut = models.CharField(max_length=20, default="EN_ATTENTE")

    def __str__(self):
        return f"{self.montant_vendeur_centimes / 100:.2f} EUR au vendeur {self.vendeur_id}"


class TypeRemboursement(models.TextChoices):
    TOTAL = "TOTAL", "Total"
    PARTIEL = "PARTIEL", "Partiel"


class Remboursement(models.Model):
    paiement = models.ForeignKey(Paiement, on_delete=models.CASCADE, related_name="remboursements")
    montant_centimes = models.PositiveIntegerField()
    motif = models.CharField(max_length=200)
    type = models.CharField(max_length=10, choices=TypeRemboursement.choices)
    declenche_par = models.ForeignKey(
        "comptes.Utilisateur", null=True, on_delete=models.SET_NULL, related_name="remboursements"
    )
    reference_stripe = models.CharField(max_length=120, blank=True)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.montant_centimes / 100:.2f} EUR — {self.motif}"


class Facture(models.Model):
    commande = models.OneToOneField(
        "commandes.Commande", on_delete=models.PROTECT, related_name="facture"
    )
    numero_facture = models.CharField(max_length=30, unique=True)
    date_emission = models.DateTimeField(auto_now_add=True)
    montant_ht_centimes = models.PositiveIntegerField()
    montant_ttc_centimes = models.PositiveIntegerField()
    taux_tva = models.DecimalField(max_digits=5, decimal_places=4, default=0.20)
    url_pdf = models.URLField(blank=True)

    def __str__(self):
        return self.numero_facture


class TypeReduction(models.TextChoices):
    POURCENTAGE = "POURCENTAGE", "Pourcentage"
    MONTANT = "MONTANT", "Montant fixe"
    FRAIS_LIVRAISON = "FRAIS_LIVRAISON", "Frais de livraison offerts"


class Promotion(models.Model):
    code = models.CharField(max_length=30, unique=True)
    # Vide = promotion de la plateforme ; renseigne = promotion de boutique.
    vendeur = models.ForeignKey(
        "comptes.Vendeur", null=True, blank=True, on_delete=models.CASCADE, related_name="promotions"
    )
    type_reduction = models.CharField(max_length=20, choices=TypeReduction.choices)
    valeur = models.DecimalField(max_digits=10, decimal_places=2)
    montant_minimum_centimes = models.PositiveIntegerField(default=0)
    date_debut = models.DateField()
    date_fin = models.DateField()
    quantite_max = models.PositiveIntegerField(null=True, blank=True)
    quantite_utilisee = models.PositiveIntegerField(default=0)
    cumulable = models.BooleanField(default=False)

    def __str__(self):
        return self.code


class UtilisationPromotion(models.Model):
    promotion = models.ForeignKey(Promotion, on_delete=models.CASCADE, related_name="utilisations")
    commande = models.ForeignKey(
        "commandes.Commande", on_delete=models.CASCADE, related_name="promotions_appliquees"
    )
    montant_applique_centimes = models.PositiveIntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["promotion", "commande"], name="promotion_une_fois_par_commande"
            )
        ]

    def __str__(self):
        return f"{self.promotion_id} sur {self.commande_id}"
