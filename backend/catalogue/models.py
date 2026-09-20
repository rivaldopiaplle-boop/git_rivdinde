"""Zone 2 du modele — catalogue et stock."""
from django.core.validators import MinValueValidator
from django.db import models


class Categorie(models.Model):
    nom = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, unique=True)
    description = models.TextField(blank=True)
    # Reflexif : une categorie peut en contenir d'autres (A13 du MCD).
    parente = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.SET_NULL, related_name="sous_categories"
    )

    class Meta:
        verbose_name = "categorie"
        verbose_name_plural = "categories"
        ordering = ["nom"]

    def __str__(self):
        return self.nom


class Produit(models.Model):
    vendeur = models.ForeignKey(
        "comptes.Vendeur", on_delete=models.CASCADE, related_name="produits"
    )
    categorie = models.ForeignKey(
        Categorie, null=True, blank=True, on_delete=models.SET_NULL, related_name="produits"
    )
    nom = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    # Tous les montants sont des ENTIERS EN CENTIMES. Un float sur de l'argent
    # finit toujours par produire un total a 0,01 pres qui ne tombe pas juste.
    prix_unitaire_centimes = models.PositiveIntegerField(validators=[MinValueValidator(1)])

    # Copie de l'URL de la photo d'ordre 1 : denormalisation assumee, sans
    # laquelle afficher cinquante produits demanderait cinquante jointures.
    # CharField et non URLField : la valeur est soit un chemin local
    # (/media/produits/x.webp en developpement), soit une URL complete
    # (Cloudinary en ligne). Le serializer se charge de la rendre absolue.
    image_principale_url = models.CharField(max_length=500, blank=True)
    poids_grammes = models.PositiveIntegerField(null=True, blank=True)

    stock_disponible = models.PositiveIntegerField(default=0)
    # Reserve pendant qu'un paiement est en cours (D-15) : le stock reellement
    # commandable vaut stock_disponible - stock_reserve.
    stock_reserve = models.PositiveIntegerField(default=0)
    seuil_alerte = models.PositiveIntegerField(default=5)

    est_visible = models.BooleanField(default=True, help_text="Masquage par le vendeur.")
    date_ajout = models.DateTimeField(auto_now_add=True)
    date_maj = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "produit"
        ordering = ["-date_ajout"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(stock_reserve__lte=models.F("stock_disponible")),
                name="stock_reserve_inferieur_au_disponible",
            )
        ]

    def __str__(self):
        return self.nom

    @property
    def stock_commandable(self):
        return self.stock_disponible - self.stock_reserve

    @property
    def est_en_rupture(self):
        return self.stock_commandable <= 0


class PhotoProduit(models.Model):
    """Un produit a de une a six photos ordonnees (D-24).

    Le modele precedent n'en prevoyait qu'une, ce qui rendait toute fiche
    produit credible impossible. Voir 03-contrats/contrat-medias.md.
    """

    produit = models.ForeignKey(Produit, on_delete=models.CASCADE, related_name="photos")
    url = models.CharField(max_length=500)
    ordre = models.PositiveSmallIntegerField(default=1)
    texte_alternatif = models.CharField(
        max_length=200, blank=True,
        help_text="Lu par les lecteurs d'ecran. Rempli automatiquement si vide.",
    )

    class Meta:
        ordering = ["ordre"]
        constraints = [
            models.UniqueConstraint(fields=["produit", "ordre"], name="ordre_photo_unique")
        ]

    def __str__(self):
        return f"Photo {self.ordre} de {self.produit_id}"


class TypeMouvement(models.TextChoices):
    VENTE = "VENTE", "Vente"
    REAPPRO = "REAPPRO", "Reapprovisionnement"
    AJUSTEMENT = "AJUSTEMENT", "Ajustement manuel"
    ANNULATION = "ANNULATION", "Annulation de commande"
    RETOUR = "RETOUR", "Retour"


class MouvementStock(models.Model):
    """Trace de tout changement de stock — exige par le scenario 4.4.

    Un ajustement manuel sans motif est refuse : c'est la seule facon de
    retrouver plus tard pourquoi un chiffre a bouge.
    """

    produit = models.ForeignKey(Produit, on_delete=models.CASCADE, related_name="mouvements")
    auteur = models.ForeignKey(
        "comptes.Utilisateur", null=True, on_delete=models.SET_NULL, related_name="mouvements_stock"
    )
    type = models.CharField(max_length=15, choices=TypeMouvement.choices)
    quantite = models.IntegerField(help_text="Signee : negative pour une sortie.")
    motif = models.CharField(max_length=200, blank=True)
    stock_apres = models.PositiveIntegerField()
    date_mouvement = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date_mouvement"]
        constraints = [
            models.CheckConstraint(
                condition=~models.Q(type="AJUSTEMENT") | ~models.Q(motif=""),
                name="ajustement_exige_un_motif",
            )
        ]

    def __str__(self):
        return f"{self.get_type_display()} {self.quantite:+d} sur {self.produit_id}"


class StatutAlerte(models.TextChoices):
    EN_ATTENTE = "EN_ATTENTE", "En attente"
    NOTIFIEE = "NOTIFIEE", "Notifiee"
    ANNULEE = "ANNULEE", "Annulee"


class AlerteDisponibilite(models.Model):
    """Le « Etre alerte quand disponible » de la decision D-06."""

    produit = models.ForeignKey(Produit, on_delete=models.CASCADE, related_name="alertes")
    utilisateur = models.ForeignKey(
        "comptes.Utilisateur", on_delete=models.CASCADE, related_name="alertes_stock"
    )
    date_demande = models.DateTimeField(auto_now_add=True)
    date_notification = models.DateTimeField(null=True, blank=True)
    statut = models.CharField(
        max_length=12, choices=StatutAlerte.choices, default=StatutAlerte.EN_ATTENTE
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["produit", "utilisateur"],
                condition=models.Q(statut="EN_ATTENTE"),
                name="une_alerte_active_par_produit_et_personne",
            )
        ]

    def __str__(self):
        return f"Alerte {self.produit_id} pour {self.utilisateur_id}"
