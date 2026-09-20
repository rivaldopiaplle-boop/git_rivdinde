"""Zone 5 du modele — livraison et logistique."""
from django.db import models


class Entrepot(models.Model):
    """Appartient a la plateforme, jamais a un vendeur (bloc A-19).

    C'est ce qui permet a plusieurs vendeurs Standard de partager une meme
    tournee : sans entrepot commun, le circuit Standard n'existe pas.
    """

    nom = models.CharField(max_length=120)
    adresse = models.ForeignKey(
        "comptes.Adresse", null=True, on_delete=models.SET_NULL, related_name="entrepots"
    )
    capacite = models.PositiveIntegerField(null=True, blank=True)
    est_actif = models.BooleanField(default=True)

    class Meta:
        verbose_name = "entrepot"

    def __str__(self):
        return self.nom


class ZoneLivraison(models.Model):
    """Au MVP, une zone est une liste de codes postaux — pas un polygone.

    PostGIS resoudrait le probleme general, mais complique l'hebergement pour
    un besoin que quelques codes postaux couvrent (stack-technique.md § 3).
    """

    nom = models.CharField(max_length=120)
    codes_postaux = models.TextField(help_text="Separes par des virgules.")
    entrepot = models.ForeignKey(
        Entrepot, null=True, blank=True, on_delete=models.SET_NULL, related_name="zones"
    )
    frais_base_centimes = models.PositiveIntegerField(default=0)
    seuil_gratuite_centimes = models.PositiveIntegerField(
        null=True, blank=True,
        help_text="Au-dela de ce montant, la livraison est offerte (D-11).",
    )

    class Meta:
        verbose_name = "zone de livraison"
        verbose_name_plural = "zones de livraison"

    def __str__(self):
        return self.nom


class StatutLivraison(models.TextChoices):
    A_ATTRIBUER = "A_ATTRIBUER", "A attribuer"
    ATTRIBUEE = "ATTRIBUEE", "Attribuee"
    RECUPEREE = "RECUPEREE", "Colis recupere"
    EN_ROUTE = "EN_ROUTE", "En route"
    LIVREE = "LIVREE", "Livree"
    ECHOUEE = "ECHOUEE", "Echouee"
    ANNULEE = "ANNULEE", "Annulee"


class Livraison(models.Model):
    commande = models.OneToOneField(
        "commandes.Commande", on_delete=models.CASCADE, related_name="livraison"
    )
    livreur = models.ForeignKey(
        "comptes.Livreur", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="livraisons",
    )
    tournee = models.ForeignKey(
        "Tournee", null=True, blank=True, on_delete=models.SET_NULL, related_name="livraisons"
    )
    adresse_livraison = models.ForeignKey(
        "comptes.Adresse", on_delete=models.PROTECT, related_name="livraisons"
    )
    statut_livraison = models.CharField(
        max_length=15, choices=StatutLivraison.choices, default=StatutLivraison.A_ATTRIBUER
    )
    distance_km = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    frais_calcules_centimes = models.PositiveIntegerField(default=0)
    remuneration_livreur_centimes = models.PositiveIntegerField(default=0)

    date_attribution = models.DateTimeField(null=True, blank=True)
    date_prise_en_charge = models.DateTimeField(null=True, blank=True)
    date_estimee = models.DateTimeField(null=True, blank=True)
    date_reelle = models.DateTimeField(null=True, blank=True)
    # Remis par le client au livreur : la preuve que le bon colis est arrive
    # a la bonne personne, sans photo ni signature.
    code_confirmation = models.CharField(max_length=8, blank=True)

    def __str__(self):
        return f"Livraison de {self.commande_id} ({self.get_statut_livraison_display()})"


class ResultatTentative(models.TextChoices):
    LIVREE = "LIVREE", "Livree"
    CLIENT_ABSENT = "CLIENT_ABSENT", "Client absent"
    ADRESSE_INTROUVABLE = "ADRESSE_INTROUVABLE", "Adresse introuvable"
    REFUSEE = "REFUSEE", "Refusee par le client"


class TentativeLivraison(models.Model):
    """Deux tentatives gratuites, puis retour (D-23)."""

    livraison = models.ForeignKey(
        Livraison, on_delete=models.CASCADE, related_name="tentatives"
    )
    numero_tentative = models.PositiveSmallIntegerField()
    resultat = models.CharField(max_length=25, choices=ResultatTentative.choices)
    commentaire = models.TextField(blank=True)
    preuve_url = models.URLField(blank=True, help_text="Photo de depot ou signature.")
    position_lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    position_lon = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    date_tentative = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["numero_tentative"]
        constraints = [
            models.UniqueConstraint(
                fields=["livraison", "numero_tentative"], name="numero_tentative_unique"
            )
        ]

    def __str__(self):
        return f"Tentative {self.numero_tentative} — {self.get_resultat_display()}"


class StatutTournee(models.TextChoices):
    BROUILLON = "BROUILLON", "Brouillon"
    PRETE = "PRETE", "Prete"
    AFFECTEE = "AFFECTEE", "Affectee"
    EN_COURS = "EN_COURS", "En cours"
    TERMINEE = "TERMINEE", "Terminee"


class Tournee(models.Model):
    """Sans elle, un livreur Standard n'aurait que des livraisons isolees —
    ce qui contredit tout le flux Standard."""

    entrepot = models.ForeignKey(Entrepot, on_delete=models.CASCADE, related_name="tournees")
    livreur = models.ForeignKey(
        "comptes.Livreur", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="tournees",
    )
    cree_par = models.ForeignKey(
        "comptes.Gestionnaire", null=True, on_delete=models.SET_NULL, related_name="tournees_creees"
    )
    zone = models.ForeignKey(
        ZoneLivraison, null=True, blank=True, on_delete=models.SET_NULL, related_name="tournees"
    )
    statut = models.CharField(
        max_length=12, choices=StatutTournee.choices, default=StatutTournee.BROUILLON
    )
    date_creation = models.DateTimeField(auto_now_add=True)
    date_debut = models.DateTimeField(null=True, blank=True)
    date_fin = models.DateTimeField(null=True, blank=True)
    nombre_arrets = models.PositiveIntegerField(default=0)
    distance_totale_km = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)

    class Meta:
        verbose_name = "tournee"
        ordering = ["-date_creation"]

    def __str__(self):
        return f"Tournee {self.pk} — {self.nombre_arrets} arrets"


class StatutArret(models.TextChoices):
    A_FAIRE = "A_FAIRE", "A faire"
    LIVRE = "LIVRE", "Livre"
    ECHOUE = "ECHOUE", "Echoue"
    REPORTE = "REPORTE", "Reporte"


class ArretTournee(models.Model):
    tournee = models.ForeignKey(Tournee, on_delete=models.CASCADE, related_name="arrets")
    livraison = models.OneToOneField(Livraison, on_delete=models.CASCADE, related_name="arret")
    ordre = models.PositiveSmallIntegerField()
    statut = models.CharField(
        max_length=10, choices=StatutArret.choices, default=StatutArret.A_FAIRE
    )
    heure_estimee = models.DateTimeField(null=True, blank=True)
    heure_reelle = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["ordre"]
        constraints = [
            models.UniqueConstraint(fields=["tournee", "ordre"], name="ordre_arret_unique")
        ]

    def __str__(self):
        return f"Arret {self.ordre} de la tournee {self.tournee_id}"
