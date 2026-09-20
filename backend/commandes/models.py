"""Zone 3 du modele — panier et commande."""
from django.db import models

from comptes.models import TypeService


class StatutPanier(models.TextChoices):
    ACTIF = "ACTIF", "Actif"
    CONVERTI = "CONVERTI", "Converti en commande"
    ABANDONNE = "ABANDONNE", "Abandonne"


class Panier(models.Model):
    """Le panier existe avant le compte : on ne demande a s'inscrire qu'au
    paiement (D-03). D'ou le client nullable et la cle de session."""

    client = models.ForeignKey(
        "comptes.Client", null=True, blank=True, on_delete=models.CASCADE, related_name="paniers"
    )
    cle_session = models.CharField(max_length=64, blank=True, db_index=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_maj = models.DateTimeField(auto_now=True)
    statut = models.CharField(
        max_length=12, choices=StatutPanier.choices, default=StatutPanier.ACTIF
    )

    class Meta:
        ordering = ["-date_maj"]

    def __str__(self):
        return f"Panier {self.pk} ({self.get_statut_display()})"


class LignePanier(models.Model):
    panier = models.ForeignKey(Panier, on_delete=models.CASCADE, related_name="lignes")
    produit = models.ForeignKey("catalogue.Produit", on_delete=models.CASCADE)
    quantite = models.PositiveIntegerField(default=1)
    # Prix au moment de l'ajout : sert uniquement a signaler au client que le
    # prix a change (R-05). Le prix qui fait foi reste celui du produit.
    prix_capture_centimes = models.PositiveIntegerField()
    date_ajout = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["panier", "produit"], name="un_produit_par_ligne")
        ]

    def __str__(self):
        return f"{self.quantite} x {self.produit_id}"


class StatutCommande(models.TextChoices):
    EN_ATTENTE_PAIEMENT = "EN_ATTENTE_PAIEMENT", "En attente de paiement"
    PAYEE = "PAYEE", "Payee"
    EN_PREPARATION = "EN_PREPARATION", "En preparation"
    PRETE = "PRETE", "Prete"
    EXPEDIEE_ENTREPOT = "EXPEDIEE_ENTREPOT", "Expediee vers l'entrepot"
    RECUE_ENTREPOT = "RECUE_ENTREPOT", "Recue a l'entrepot"
    EN_TOURNEE = "EN_TOURNEE", "En tournee"
    EN_LIVRAISON = "EN_LIVRAISON", "En livraison"
    LIVREE = "LIVREE", "Livree"
    ANNULEE = "ANNULEE", "Annulee"
    REMBOURSEE = "REMBOURSEE", "Remboursee"
    ECHEC_LIVRAISON = "ECHEC_LIVRAISON", "Echec de livraison"


class Commande(models.Model):
    """Une commande = un seul mode de service, un seul paiement, une livraison.

    Un panier mixte donne donc PLUSIEURS commandes (D-10) : une par vendeur
    Express, plus une seule commande Standard multi-vendeur.
    """

    numero_commande = models.CharField(max_length=20, unique=True)
    client = models.ForeignKey(
        "comptes.Client", on_delete=models.PROTECT, related_name="commandes"
    )
    adresse_livraison = models.ForeignKey(
        "comptes.Adresse", on_delete=models.PROTECT, related_name="commandes"
    )
    panier_origine = models.ForeignKey(
        Panier, null=True, blank=True, on_delete=models.SET_NULL, related_name="commandes"
    )
    type_service = models.CharField(max_length=10, choices=TypeService.choices)
    statut_actuel = models.CharField(
        max_length=25, choices=StatutCommande.choices,
        default=StatutCommande.EN_ATTENTE_PAIEMENT,
    )

    montant_produits_centimes = models.PositiveIntegerField(default=0)
    montant_livraison_centimes = models.PositiveIntegerField(default=0)
    montant_remise_centimes = models.PositiveIntegerField(default=0)
    montant_total_centimes = models.PositiveIntegerField(default=0)

    date_commande = models.DateTimeField(auto_now_add=True)
    date_livraison_estimee = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-date_commande"]

    def __str__(self):
        return self.numero_commande


class StatutPreparation(models.TextChoices):
    A_PREPARER = "A_PREPARER", "A preparer"
    EN_PREPARATION = "EN_PREPARATION", "En preparation"
    PRETE = "PRETE", "Prete"
    EXPEDIEE = "EXPEDIEE", "Expediee"
    ANNULEE = "ANNULEE", "Annulee"


class SousCommande(models.Model):
    """La part d'une commande revenant a UN vendeur.

    Une commande Express en a exactement une : cela permet d'ecrire un seul
    code de preparation pour les deux modes de service.
    """

    commande = models.ForeignKey(Commande, on_delete=models.CASCADE, related_name="sous_commandes")
    vendeur = models.ForeignKey(
        "comptes.Vendeur", on_delete=models.PROTECT, related_name="sous_commandes"
    )
    entrepot = models.ForeignKey(
        "livraisons.Entrepot", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="colis_recus",
    )
    statut_preparation = models.CharField(
        max_length=15, choices=StatutPreparation.choices, default=StatutPreparation.A_PREPARER
    )
    montant_vendeur_centimes = models.PositiveIntegerField(default=0)
    montant_commission_centimes = models.PositiveIntegerField(default=0)
    date_expedition_entrepot = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["commande", "vendeur"], name="un_vendeur_une_fois_par_commande"
            )
        ]

    def __str__(self):
        return f"{self.commande_id} — part de {self.vendeur_id}"


class LigneCommande(models.Model):
    """Le nom et le prix sont RECOPIES, jamais lus depuis le produit.

    Une commande passee ne change plus, meme si le produit est renomme,
    reevalue ou masque. C'est la difference entre une facture et un rapport.
    """

    sous_commande = models.ForeignKey(
        SousCommande, on_delete=models.CASCADE, related_name="lignes"
    )
    produit = models.ForeignKey("catalogue.Produit", null=True, on_delete=models.SET_NULL)
    nom_produit_capture = models.CharField(max_length=200)
    prix_unitaire_centimes = models.PositiveIntegerField()
    quantite = models.PositiveIntegerField()
    sous_total_centimes = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.quantite} x {self.nom_produit_capture}"


class TypeObjetSuivi(models.TextChoices):
    COMMANDE = "COMMANDE", "Commande"
    LIVRAISON = "LIVRAISON", "Livraison"


class HistoriqueStatut(models.Model):
    """Qui a change quoi, quand, et pourquoi. Jamais de statut modifie en silence."""

    type_objet = models.CharField(max_length=12, choices=TypeObjetSuivi.choices)
    id_objet = models.PositiveIntegerField()
    statut_avant = models.CharField(max_length=25, blank=True)
    statut_apres = models.CharField(max_length=25)
    utilisateur = models.ForeignKey(
        "comptes.Utilisateur", null=True, on_delete=models.SET_NULL,
        related_name="changements_de_statut",
    )
    commentaire = models.TextField(blank=True)
    date_changement = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date_changement"]
        indexes = [models.Index(fields=["type_objet", "id_objet"])]

    def __str__(self):
        return f"{self.type_objet} {self.id_objet} : {self.statut_apres}"
