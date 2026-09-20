"""Les serializers sont les DTO du projet banque : ils valident ce qui entre
et decident de ce qui sort. Rien d'autre ne doit franchir la frontiere HTTP.
"""
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from rest_framework import serializers

from .models import (
    Adresse,
    Client,
    Gestionnaire,
    Livreur,
    Role,
    StatutCompte,
    TypeGestionnaire,
    Utilisateur,
    Vendeur,
)


class UtilisateurSerializer(serializers.ModelSerializer):
    """Ce que le front recoit sur /moi. Jamais le mot de passe, meme hache."""

    class Meta:
        model = Utilisateur
        fields = [
            "id", "email", "nom", "prenom", "telephone",
            "role", "statut_compte", "date_inscription",
        ]
        read_only_fields = ["id", "role", "statut_compte", "date_inscription"]


class _InscriptionBase(serializers.Serializer):
    email = serializers.EmailField()
    mot_de_passe = serializers.CharField(write_only=True, validators=[validate_password])
    nom = serializers.CharField(max_length=100)
    prenom = serializers.CharField(max_length=100)
    telephone = serializers.CharField(max_length=30, required=False, allow_blank=True)

    role = None
    statut_a_la_creation = StatutCompte.ACTIF

    def validate_email(self, valeur):
        if Utilisateur.objects.filter(email__iexact=valeur).exists():
            # Message volontairement explicite : cacher qu'un compte existe
            # n'empeche pas de le decouvrir, et bloque l'utilisateur legitime.
            raise serializers.ValidationError("Un compte existe deja avec cette adresse.")
        return valeur.lower()

    def creer_profil(self, utilisateur, donnees):
        raise NotImplementedError

    @transaction.atomic
    def create(self, donnees):
        utilisateur = Utilisateur.objects.create_user(
            email=donnees["email"],
            password=donnees["mot_de_passe"],
            nom=donnees["nom"],
            prenom=donnees["prenom"],
            telephone=donnees.get("telephone", ""),
            role=self.role,
            statut_compte=self.statut_a_la_creation,
        )
        self.creer_profil(utilisateur, donnees)
        return utilisateur


class InscriptionClientSerializer(_InscriptionBase):
    """Auto-inscription libre, compte actif immediatement (D-02)."""

    role = Role.CLIENT
    consentement_marketing = serializers.BooleanField(required=False, default=False)

    def creer_profil(self, utilisateur, donnees):
        Client.objects.create(
            utilisateur=utilisateur,
            consentement_marketing=donnees.get("consentement_marketing", False),
        )


class InscriptionVendeurSerializer(_InscriptionBase):
    """Candidature : le compte existe mais reste EN_ATTENTE_VALIDATION.

    Tant qu'un admin n'a pas verifie, aucun produit ne peut etre publie.
    """

    role = Role.VENDEUR
    statut_a_la_creation = StatutCompte.EN_ATTENTE
    nom_boutique = serializers.CharField(max_length=150)
    type_activite = serializers.ChoiceField(choices=["EXPRESS", "STANDARD"])
    siret = serializers.CharField(max_length=20, required=False, allow_blank=True)

    def creer_profil(self, utilisateur, donnees):
        Vendeur.objects.create(
            utilisateur=utilisateur,
            nom_boutique=donnees["nom_boutique"],
            type_activite=donnees["type_activite"],
            siret=donnees.get("siret", ""),
        )


class InscriptionLivreurSerializer(_InscriptionBase):
    role = Role.LIVREUR
    statut_a_la_creation = StatutCompte.EN_ATTENTE
    vehicule = serializers.ChoiceField(
        choices=["VELO", "SCOOTER", "VOITURE", "CAMIONNETTE"], default="VELO"
    )
    mode_livraison = serializers.ChoiceField(choices=["EXPRESS", "STANDARD"])

    def creer_profil(self, utilisateur, donnees):
        Livreur.objects.create(
            utilisateur=utilisateur,
            vehicule=donnees.get("vehicule", "VELO"),
            mode_livraison=donnees["mode_livraison"],
        )


class CreationGestionnaireSerializer(_InscriptionBase):
    """Cree par son vendeur ou par un admin — jamais d'auto-inscription (D-02).

    Le vendeur qui appelle est deduit du jeton, il n'est pas dans la charge
    utile : sinon n'importe quel vendeur creerait du personnel chez un autre.
    """

    role = Role.GESTIONNAIRE
    type_gestionnaire = serializers.ChoiceField(choices=TypeGestionnaire.values)
    id_entrepot = serializers.IntegerField(required=False)

    def creer_profil(self, utilisateur, donnees):
        Gestionnaire.objects.create(
            utilisateur=utilisateur,
            type_gestionnaire=donnees["type_gestionnaire"],
            vendeur=self.context.get("vendeur"),
            entrepot_id=donnees.get("id_entrepot"),
        )


class AdresseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Adresse
        fields = [
            "id", "libelle", "rue", "complement", "ville", "code_postal",
            "pays", "latitude", "longitude", "instructions_livraison",
        ]
        read_only_fields = ["id", "latitude", "longitude"]


class VendeurSerializer(serializers.ModelSerializer):
    utilisateur = UtilisateurSerializer(read_only=True)

    class Meta:
        model = Vendeur
        fields = [
            "id", "utilisateur", "nom_boutique", "type_activite",
            "rayon_livraison_km", "siret", "description", "logo_url",
            "note_moyenne", "statut_validation",
        ]
        read_only_fields = ["id", "utilisateur", "note_moyenne", "statut_validation"]


class LivreurSerializer(serializers.ModelSerializer):
    utilisateur = UtilisateurSerializer(read_only=True)

    class Meta:
        model = Livreur
        fields = [
            "id", "utilisateur", "vehicule", "mode_livraison",
            "statut_validation", "statut_disponibilite", "note_moyenne",
        ]
        read_only_fields = ["id", "utilisateur", "statut_validation", "note_moyenne"]


class MoiSerializer(serializers.Serializer):
    """Le profil complet renvoye a la connexion : l'utilisateur, plus la partie
    metier qui depend de son role. Le front n'a ainsi qu'un appel a faire pour
    savoir quoi afficher."""

    utilisateur = UtilisateurSerializer()
    profil = serializers.SerializerMethodField()

    def get_profil(self, donnees):
        utilisateur = donnees["utilisateur"]
        if utilisateur.role == Role.VENDEUR:
            profil = getattr(utilisateur, "profil_vendeur", None)
            return VendeurSerializer(profil).data if profil else None
        if utilisateur.role == Role.LIVREUR:
            profil = getattr(utilisateur, "profil_livreur", None)
            return LivreurSerializer(profil).data if profil else None
        if utilisateur.role == Role.GESTIONNAIRE:
            profil = getattr(utilisateur, "profil_gestionnaire", None)
            if not profil:
                return None
            return {
                "id": profil.id,
                "type_gestionnaire": profil.type_gestionnaire,
                "id_vendeur": profil.vendeur_id,
                "id_entrepot": profil.entrepot_id,
            }
        if utilisateur.role == Role.ADMIN:
            profil = getattr(utilisateur, "profil_admin", None)
            return {"id": profil.id, "niveau": profil.niveau} if profil else None
        profil = getattr(utilisateur, "profil_client", None)
        if not profil:
            return None
        return {
            "id": profil.id,
            "consentement_marketing": profil.consentement_marketing,
        }


class ConnexionSerializer(serializers.Serializer):
    """Les noms des champs sont en francais cote API, comme tout le contrat.

    On ne reutilise pas le serializer de simplejwt : il impose `username` et
    `password`, et il refuse un compte `is_active=False` sans expliquer
    pourquoi. Ici, un vendeur en attente doit pouvoir se connecter et voir son
    ecran d'attente (contrat-api.md).
    """

    email = serializers.EmailField()
    mot_de_passe = serializers.CharField(write_only=True)
