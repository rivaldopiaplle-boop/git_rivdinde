"""Zone 6 du modele — avis, litiges, notifications, audit."""
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class CibleAvis(models.TextChoices):
    PRODUIT = "PRODUIT", "Produit"
    VENDEUR = "VENDEUR", "Boutique"
    LIVREUR = "LIVREUR", "Livreur"


class StatutModeration(models.TextChoices):
    PUBLIE = "PUBLIE", "Publie"
    SIGNALE = "SIGNALE", "Signale"
    MASQUE = "MASQUE", "Masque"


class Avis(models.Model):
    """La commande est obligatoire : on ne note que ce qu'on a recu (R-06).

    La cible est polymorphe — un avis vise soit un produit, soit une boutique,
    soit un livreur, jamais deux a la fois.
    """

    client = models.ForeignKey("comptes.Client", on_delete=models.CASCADE, related_name="avis")
    commande = models.ForeignKey(
        "commandes.Commande", on_delete=models.CASCADE, related_name="avis"
    )
    cible = models.CharField(max_length=10, choices=CibleAvis.choices)
    id_cible = models.PositiveIntegerField()
    note = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    commentaire = models.TextField(blank=True)
    date_avis = models.DateTimeField(auto_now_add=True)
    statut_moderation = models.CharField(
        max_length=10, choices=StatutModeration.choices, default=StatutModeration.PUBLIE
    )

    class Meta:
        verbose_name = "avis"
        verbose_name_plural = "avis"
        indexes = [models.Index(fields=["cible", "id_cible"])]
        constraints = [
            models.UniqueConstraint(
                fields=["client", "commande", "cible", "id_cible"], name="un_avis_par_cible"
            )
        ]

    def __str__(self):
        return f"{self.note}/5 sur {self.get_cible_display().lower()} {self.id_cible}"


class MotifLitige(models.TextChoices):
    NON_CONFORME = "NON_CONFORME", "Produit non conforme"
    ENDOMMAGE = "ENDOMMAGE", "Produit endommage"
    INCOMPLET = "INCOMPLET", "Commande incomplete"
    NON_RECU = "NON_RECU", "Jamais recu"


class StatutLitige(models.TextChoices):
    OUVERT = "OUVERT", "Ouvert"
    EN_COURS = "EN_COURS", "En cours d'examen"
    RESOLU = "RESOLU", "Resolu"
    REJETE = "REJETE", "Rejete"


class Litige(models.Model):
    commande = models.ForeignKey(
        "commandes.Commande", on_delete=models.CASCADE, related_name="litiges"
    )
    client = models.ForeignKey("comptes.Client", on_delete=models.CASCADE, related_name="litiges")
    admin_traitant = models.ForeignKey(
        "comptes.Administrateur", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="litiges_traites",
    )
    motif = models.CharField(max_length=15, choices=MotifLitige.choices)
    description = models.TextField()
    preuves_urls = models.TextField(blank=True, help_text="URLs separees par des virgules.")
    statut = models.CharField(
        max_length=10, choices=StatutLitige.choices, default=StatutLitige.OUVERT
    )
    resolution = models.TextField(blank=True)
    montant_rembourse_centimes = models.PositiveIntegerField(default=0)
    date_ouverture = models.DateTimeField(auto_now_add=True)
    date_resolution = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-date_ouverture"]

    def __str__(self):
        return f"Litige {self.pk} — {self.get_motif_display()}"


class CanalNotification(models.TextChoices):
    IN_APP = "IN_APP", "Dans l'application"
    EMAIL = "EMAIL", "Courriel"
    PUSH = "PUSH", "Notification poussee"


class Notification(models.Model):
    """Rattachee a UTILISATEUR et non a « client » : tous les roles sont
    notifiables. Le canal in-app est toujours actif — une information critique
    n'a jamais un canal unique (scenario 12.1)."""

    utilisateur = models.ForeignKey(
        "comptes.Utilisateur", on_delete=models.CASCADE, related_name="notifications"
    )
    type = models.CharField(max_length=40)
    titre = models.CharField(max_length=150)
    contenu = models.TextField()
    lien_action = models.CharField(max_length=200, blank=True)
    canal = models.CharField(
        max_length=10, choices=CanalNotification.choices, default=CanalNotification.IN_APP
    )
    date_envoi = models.DateTimeField(auto_now_add=True)
    date_lecture = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-date_envoi"]

    def __str__(self):
        return f"{self.titre} ({self.get_canal_display()})"


class JournalAudit(models.Model):
    """Exige par D-13 : aucune suppression physique, tout changement est trace."""

    utilisateur = models.ForeignKey(
        "comptes.Utilisateur", null=True, on_delete=models.SET_NULL, related_name="actions"
    )
    action = models.CharField(max_length=80)
    type_objet = models.CharField(max_length=60)
    id_objet = models.PositiveIntegerField(null=True, blank=True)
    donnees_avant = models.JSONField(null=True, blank=True)
    donnees_apres = models.JSONField(null=True, blank=True)
    adresse_ip = models.GenericIPAddressField(null=True, blank=True)
    date_action = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "entree du journal d'audit"
        verbose_name_plural = "journal d'audit"
        ordering = ["-date_action"]
        indexes = [models.Index(fields=["type_objet", "id_objet"])]

    def __str__(self):
        return f"{self.action} sur {self.type_objet} {self.id_objet}"
