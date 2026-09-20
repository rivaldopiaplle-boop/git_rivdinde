"""Le catalogue est public — c'est une decision, pas un oubli (D-03).

Un visiteur doit pouvoir tout regarder avant de decider de s'inscrire. Le
compte n'est exige qu'au moment de payer.
"""
import pytest
from django.urls import reverse

from catalogue.models import Categorie, Produit
from comptes.models import (
    Adresse,
    StatutCompte,
    StatutValidation,
    TypeService,
    Utilisateur,
    Vendeur,
)

MOT_DE_PASSE = "UnMotDePasseSolide!2026"

# Lyon 2e, l'adresse de Lea dans le jeu de demonstration.
LYON = {"lat": 45.7550, "lon": 4.8320}
# Marseille : hors de tout rayon Express lyonnais.
MARSEILLE = {"lat": 43.2965, "lon": 5.3698}


def creer_vendeur(nom, service, valide=True, lat=45.7545, lon=4.8480, rayon=6):
    utilisateur = Utilisateur.objects.create_user(
        email=f"{nom.lower().replace(' ', '')}@exemple.fr", password=MOT_DE_PASSE,
        nom=nom, prenom="Test", role="VENDEUR", statut_compte=StatutCompte.ACTIF,
    )
    adresse = Adresse.objects.create(rue="1 rue Test", ville="Lyon", code_postal="69003",
                                     latitude=lat, longitude=lon)
    return Vendeur.objects.create(
        utilisateur=utilisateur, nom_boutique=nom, type_activite=service,
        adresse=adresse, rayon_livraison_km=rayon,
        statut_validation=StatutValidation.VALIDE if valide else StatutValidation.EN_ATTENTE,
    )


def creer_produit(vendeur, nom="Article", stock=10, visible=True):
    return Produit.objects.create(
        vendeur=vendeur, nom=nom, prix_unitaire_centimes=1000,
        stock_disponible=stock, est_visible=visible,
    )


@pytest.fixture
def catalogue(db):
    express = creer_vendeur("Chez Karim", TypeService.EXPRESS)
    standard = creer_vendeur("TechSophie", TypeService.STANDARD)
    creer_produit(express, "Bol de ramen")
    creer_produit(standard, "Casque audio")
    return {"express": express, "standard": standard}


# ── Acces public ─────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_le_catalogue_repond_sans_aucun_jeton(client, catalogue):
    reponse = client.get(reverse("liste-produits"))

    assert reponse.status_code == 200, "un visiteur doit pouvoir regarder avant de s'inscrire"


@pytest.mark.django_db
def test_la_fiche_produit_est_publique(client, catalogue):
    produit = Produit.objects.get(nom="Casque audio")

    reponse = client.get(reverse("detail-produit", args=[produit.id]))

    assert reponse.status_code == 200
    assert reponse.json()["data"]["nom"] == "Casque audio"


@pytest.mark.django_db
def test_les_categories_et_boutiques_sont_publiques(client, catalogue):
    assert client.get(reverse("liste-categories")).status_code == 200
    assert client.get(reverse("liste-boutiques")).status_code == 200


# ── Le filtrage geographique, coeur de la decision D-09 ──────────────────

@pytest.mark.django_db
def test_sans_position_seul_le_standard_est_visible(client, catalogue):
    noms = [p["nom"] for p in client.get(reverse("liste-produits")).json()["data"]]

    assert "Casque audio" in noms
    assert "Bol de ramen" not in noms, (
        "sans savoir ou est le client, montrer un restaurant serait mentir sur "
        "la livraison"
    )


@pytest.mark.django_db
def test_dans_le_rayon_l_express_apparait_avec_sa_distance(client, catalogue):
    donnees = client.get(reverse("liste-produits"), LYON).json()["data"]

    ramen = next(p for p in donnees if p["nom"] == "Bol de ramen")
    assert ramen["distance_km"] is not None
    assert ramen["distance_km"] < 6


@pytest.mark.django_db
def test_hors_du_rayon_l_express_disparait_completement(client, catalogue):
    noms = [p["nom"] for p in client.get(reverse("liste-produits"), MARSEILLE).json()["data"]]

    assert "Bol de ramen" not in noms
    assert "Casque audio" in noms, "le Standard, lui, n'a pas de restriction de distance"


# ── Ce qui ne doit pas apparaitre ────────────────────────────────────────

@pytest.mark.django_db
def test_un_vendeur_non_valide_n_a_aucun_produit_au_catalogue(client, db):
    vendeur = creer_vendeur("Fleurs d'Ines", TypeService.STANDARD, valide=False)
    creer_produit(vendeur, "Bouquet")

    noms = [p["nom"] for p in client.get(reverse("liste-produits")).json()["data"]]

    assert "Bouquet" not in noms


@pytest.mark.django_db
def test_un_produit_masque_disparait_du_catalogue(client, catalogue):
    creer_produit(catalogue["standard"], "Brouillon", visible=False)

    noms = [p["nom"] for p in client.get(reverse("liste-produits")).json()["data"]]

    assert "Brouillon" not in noms


@pytest.mark.django_db
def test_un_produit_en_rupture_reste_visible_mais_indisponible(client, catalogue):
    creer_produit(catalogue["standard"], "Epuise", stock=0)

    donnees = client.get(reverse("liste-produits")).json()["data"]

    epuise = next(p for p in donnees if p["nom"] == "Epuise")
    # Il reste au catalogue : c'est ce qui permet le bouton gele et l'alerte
    # de retour en stock (D-06). Le masquer serait perdre le client.
    assert epuise["disponible"] is False


# ── Ecriture : reservee au vendeur, et seulement chez lui ────────────────

@pytest.mark.django_db
def test_un_visiteur_ne_peut_pas_publier(client, catalogue):
    reponse = client.post(reverse("mes-produits"), {}, content_type="application/json")

    assert reponse.status_code == 401


@pytest.mark.django_db
def test_un_vendeur_ne_modifie_pas_le_produit_d_un_autre(client, catalogue):
    produit_de_sophie = Produit.objects.get(nom="Casque audio")
    jeton = client.post(
        reverse("connexion"),
        {"email": catalogue["express"].utilisateur.email, "mot_de_passe": MOT_DE_PASSE},
        content_type="application/json",
    ).json()["data"]["acces"]

    reponse = client.patch(
        reverse("modifier-produit", args=[produit_de_sophie.id]),
        {"nom": "Detourne"},
        content_type="application/json",
        headers={"Authorization": f"Bearer {jeton}"},
    )

    # 404 et non 403 : repondre « interdit » revelerait que ce produit existe.
    assert reponse.status_code == 404
    produit_de_sophie.refresh_from_db()
    assert produit_de_sophie.nom == "Casque audio"


@pytest.mark.django_db
def test_un_vendeur_publie_dans_sa_propre_boutique(client, catalogue):
    Categorie.objects.create(nom="Plats", slug="plats")
    jeton = client.post(
        reverse("connexion"),
        {"email": catalogue["express"].utilisateur.email, "mot_de_passe": MOT_DE_PASSE},
        content_type="application/json",
    ).json()["data"]["acces"]

    reponse = client.post(
        reverse("mes-produits"),
        {"nom": "Nouveau plat", "prix_unitaire_centimes": 1500, "stock_disponible": 10},
        content_type="application/json",
        headers={"Authorization": f"Bearer {jeton}"},
    )

    assert reponse.status_code == 201
    # Le vendeur vient du jeton, jamais de la charge utile.
    assert Produit.objects.get(nom="Nouveau plat").vendeur_id == catalogue["express"].id


@pytest.mark.django_db
def test_un_vendeur_en_attente_ne_publie_pas(client, db):
    vendeur = creer_vendeur("Fleurs d'Ines", TypeService.STANDARD, valide=False)
    vendeur.utilisateur.statut_compte = StatutCompte.ACTIF
    vendeur.utilisateur.save()
    jeton = client.post(
        reverse("connexion"),
        {"email": vendeur.utilisateur.email, "mot_de_passe": MOT_DE_PASSE},
        content_type="application/json",
    ).json()["data"]["acces"]

    reponse = client.post(
        reverse("mes-produits"),
        {"nom": "Bouquet", "prix_unitaire_centimes": 2000},
        content_type="application/json",
        headers={"Authorization": f"Bearer {jeton}"},
    )

    assert reponse.status_code == 403
