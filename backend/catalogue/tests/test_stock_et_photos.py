"""Le stock ne bouge jamais en silence — scenario 4.4.

Chaque changement laisse un mouvement trace, avec son auteur et son motif.
Un ajustement manuel sans motif est refuse : c'est la seule facon de retrouver
le lendemain pourquoi un chiffre a bouge.
"""
import io

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from PIL import Image

from catalogue.models import MouvementStock, PhotoProduit, Produit, TypeMouvement
from comptes.models import (
    Gestionnaire,
    StatutCompte,
    StatutValidation,
    TypeGestionnaire,
    TypeService,
    Utilisateur,
    Vendeur,
)

MOT_DE_PASSE = "UnMotDePasseSolide!2026"


def jeton(client, email):
    return client.post(
        reverse("connexion"), {"email": email, "mot_de_passe": MOT_DE_PASSE},
        content_type="application/json",
    ).json()["data"]["acces"]


def entete(client, email):
    return {"Authorization": f"Bearer {jeton(client, email)}"}


@pytest.fixture
def boutique(db):
    utilisateur = Utilisateur.objects.create_user(
        email="karim@exemple.fr", password=MOT_DE_PASSE, nom="Benali", prenom="Karim",
        role="VENDEUR", statut_compte=StatutCompte.ACTIF,
    )
    return Vendeur.objects.create(
        utilisateur=utilisateur, nom_boutique="Chez Karim",
        type_activite=TypeService.EXPRESS, statut_validation=StatutValidation.VALIDE,
    )


@pytest.fixture
def produit(boutique):
    return Produit.objects.create(
        vendeur=boutique, nom="Ramen", prix_unitaire_centimes=1290,
        stock_disponible=10, seuil_alerte=5,
    )


def image_de_test(largeur=800, hauteur=800, format_="JPEG", nom="photo.jpg"):
    tampon = io.BytesIO()
    Image.new("RGB", (largeur, hauteur), (200, 120, 40)).save(tampon, format_)
    tampon.seek(0)
    return SimpleUploadedFile(nom, tampon.read(), content_type=f"image/{format_.lower()}")


# ── Le stock ─────────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_un_reapprovisionnement_augmente_le_stock_et_laisse_une_trace(client, produit):
    reponse = client.patch(
        reverse("modifier-stock", args=[produit.id]),
        {"quantite": 5, "type": TypeMouvement.REAPPRO, "motif": "Livraison du matin"},
        content_type="application/json", headers=entete(client, "karim@exemple.fr"),
    )

    assert reponse.status_code == 200
    assert reponse.json()["data"]["stock_disponible"] == 15
    mouvement = MouvementStock.objects.get()
    assert mouvement.quantite == 5
    assert mouvement.stock_apres == 15
    assert mouvement.auteur.email == "karim@exemple.fr"


@pytest.mark.django_db
def test_un_ajustement_sans_motif_est_refuse(client, produit):
    reponse = client.patch(
        reverse("modifier-stock", args=[produit.id]),
        {"quantite": -2, "type": TypeMouvement.AJUSTEMENT, "motif": "   "},
        content_type="application/json", headers=entete(client, "karim@exemple.fr"),
    )

    assert reponse.status_code == 400
    produit.refresh_from_db()
    assert produit.stock_disponible == 10, "le stock ne doit pas avoir bouge"
    assert not MouvementStock.objects.exists()


@pytest.mark.django_db
def test_le_stock_ne_peut_pas_devenir_negatif(client, produit):
    reponse = client.patch(
        reverse("modifier-stock", args=[produit.id]),
        {"quantite": -99, "type": TypeMouvement.AJUSTEMENT, "motif": "Inventaire"},
        content_type="application/json", headers=entete(client, "karim@exemple.fr"),
    )

    assert reponse.status_code == 400
    produit.refresh_from_db()
    assert produit.stock_disponible == 10


@pytest.mark.django_db
def test_le_stock_ne_descend_pas_sous_ce_qui_est_reserve(client, produit):
    # Trois exemplaires sont retenus par des paiements en cours (D-15).
    produit.stock_reserve = 3
    produit.save()

    reponse = client.patch(
        reverse("modifier-stock", args=[produit.id]),
        {"quantite": -9, "type": TypeMouvement.AJUSTEMENT, "motif": "Casse"},
        content_type="application/json", headers=entete(client, "karim@exemple.fr"),
    )

    assert reponse.status_code == 400
    assert "reserv" in reponse.json()["erreur"]["message"].lower()


@pytest.mark.django_db
def test_le_personnel_du_vendeur_peut_ajuster_le_stock(client, boutique, produit):
    """Le gestionnaire constate les casses : lui refuser l'ajustement
    obligerait a deranger le vendeur a chaque fois (D-04)."""
    compte = Utilisateur.objects.create_user(
        email="nadia@exemple.fr", password=MOT_DE_PASSE, nom="Sow", prenom="Nadia",
        role="GESTIONNAIRE", statut_compte=StatutCompte.ACTIF,
    )
    Gestionnaire.objects.create(
        utilisateur=compte, type_gestionnaire=TypeGestionnaire.STAFF_VENDEUR, vendeur=boutique
    )

    reponse = client.patch(
        reverse("modifier-stock", args=[produit.id]),
        {"quantite": -1, "type": TypeMouvement.AJUSTEMENT, "motif": "Assiette cassee"},
        content_type="application/json", headers=entete(client, "nadia@exemple.fr"),
    )

    assert reponse.status_code == 200
    assert MouvementStock.objects.get().auteur.email == "nadia@exemple.fr"


@pytest.mark.django_db
def test_un_vendeur_ne_touche_pas_au_stock_d_un_autre(client, produit):
    autre = Utilisateur.objects.create_user(
        email="sophie@exemple.fr", password=MOT_DE_PASSE, nom="Leroy", prenom="Sophie",
        role="VENDEUR", statut_compte=StatutCompte.ACTIF,
    )
    Vendeur.objects.create(
        utilisateur=autre, nom_boutique="TechSophie", type_activite=TypeService.STANDARD,
        statut_validation=StatutValidation.VALIDE,
    )

    reponse = client.patch(
        reverse("modifier-stock", args=[produit.id]),
        {"quantite": 100, "type": TypeMouvement.REAPPRO, "motif": ""},
        content_type="application/json", headers=entete(client, "sophie@exemple.fr"),
    )

    assert reponse.status_code == 404


@pytest.mark.django_db
def test_l_historique_des_mouvements_est_consultable(client, produit):
    en_tete = entete(client, "karim@exemple.fr")
    for quantite in (5, -2):
        client.patch(
            reverse("modifier-stock", args=[produit.id]),
            {"quantite": quantite, "type": TypeMouvement.AJUSTEMENT, "motif": "Inventaire"},
            content_type="application/json", headers=en_tete,
        )

    donnees = client.get(reverse("mouvements-produit", args=[produit.id]),
                         headers=en_tete).json()["data"]

    assert len(donnees) == 2
    assert donnees[0]["auteur"] != "—"


# ── Les photos ───────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_un_vendeur_televerse_une_photo(client, produit, stockage_local):

    reponse = client.post(
        reverse("televerser-photos", args=[produit.id]),
        {"photos": image_de_test()},
        headers=entete(client, "karim@exemple.fr"),
    )

    assert reponse.status_code == 201
    photo = PhotoProduit.objects.get()
    assert photo.ordre == 1
    # Le texte alternatif est rempli tout seul : une image sans description est
    # invisible pour qui n'a pas l'ecran.
    assert produit.nom in photo.texte_alternatif
    produit.refresh_from_db()
    assert produit.image_principale_url == photo.url


@pytest.mark.django_db
def test_une_image_trop_petite_est_refusee_avec_un_message_clair(client, produit):

    reponse = client.post(
        reverse("televerser-photos", args=[produit.id]),
        {"photos": image_de_test(largeur=100, hauteur=100)},
        headers=entete(client, "karim@exemple.fr"),
    )

    assert reponse.status_code == 400
    assert "600" in reponse.json()["erreur"]["message"]


@pytest.mark.django_db
def test_un_fichier_qui_n_est_pas_une_image_est_refuse(client, produit):
    faux = SimpleUploadedFile("photo.jpg", b"ceci n'est pas une image", content_type="image/jpeg")

    reponse = client.post(
        reverse("televerser-photos", args=[produit.id]), {"photos": faux},
        headers=entete(client, "karim@exemple.fr"),
    )

    # On ne regarde jamais l'extension : c'est le moyen le plus classique de
    # faire televerser autre chose qu'une image.
    assert reponse.status_code == 400


@pytest.mark.django_db
def test_la_photo_est_convertie_et_debarrassee_de_ses_metadonnees(client, produit,
                                                                  stockage_local):

    client.post(
        reverse("televerser-photos", args=[produit.id]),
        {"photos": image_de_test(largeur=1600, hauteur=1200, format_="PNG", nom="photo.png")},
        headers=entete(client, "karim@exemple.fr"),
    )

    fichier = next((stockage_local.MEDIA_ROOT / "produits").iterdir())
    image = Image.open(fichier)
    assert image.format == "WEBP"
    assert image.size == (900, 675), "recadre au format de la grille"
    assert not image.getexif(), "aucune metadonnee ne doit subsister"


@pytest.mark.django_db
def test_reordonner_change_la_photo_principale(client, produit, stockage_local):
    en_tete = entete(client, "karim@exemple.fr")
    for nom in ("une.jpg", "deux.jpg"):
        client.post(reverse("televerser-photos", args=[produit.id]),
                    {"photos": image_de_test(nom=nom)}, headers=en_tete)

    photos = list(PhotoProduit.objects.order_by("ordre"))
    client.patch(
        reverse("ordonner-photos", args=[produit.id]),
        {"ordre": [photos[1].id, photos[0].id]},
        content_type="application/json", headers=en_tete,
    )

    produit.refresh_from_db()
    assert produit.image_principale_url == photos[1].url


@pytest.mark.django_db
def test_un_vendeur_ne_televerse_pas_chez_un_autre(client, produit):
    autre = Utilisateur.objects.create_user(
        email="sophie@exemple.fr", password=MOT_DE_PASSE, nom="Leroy", prenom="Sophie",
        role="VENDEUR", statut_compte=StatutCompte.ACTIF,
    )
    Vendeur.objects.create(
        utilisateur=autre, nom_boutique="TechSophie", type_activite=TypeService.STANDARD,
        statut_validation=StatutValidation.VALIDE,
    )

    reponse = client.post(
        reverse("televerser-photos", args=[produit.id]), {"photos": image_de_test()},
        headers=entete(client, "sophie@exemple.fr"),
    )

    assert reponse.status_code == 404
    assert not PhotoProduit.objects.exists()
