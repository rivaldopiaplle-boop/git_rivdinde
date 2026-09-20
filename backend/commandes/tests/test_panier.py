"""Le panier existe avant le compte — decision D-03.

Un visiteur remplit son panier sans s'inscrire ; le compte n'est exige qu'au
moment de payer. Et surtout : le panier le suit quand il se connecte, sinon il
le retrouve vide et il ne revient pas.
"""
import pytest
from django.urls import reverse

from catalogue.models import Produit
from commandes.models import Panier, StatutPanier
from comptes.models import (
    Adresse,
    Client,
    StatutCompte,
    StatutValidation,
    TypeService,
    Utilisateur,
    Vendeur,
)

MOT_DE_PASSE = "UnMotDePasseSolide!2026"
SESSION = "session-de-test-0001"


@pytest.fixture
def boutique(db):
    utilisateur = Utilisateur.objects.create_user(
        email="sophie@exemple.fr", password=MOT_DE_PASSE, nom="Leroy", prenom="Sophie",
        role="VENDEUR", statut_compte=StatutCompte.ACTIF,
    )
    adresse = Adresse.objects.create(rue="1 rue Test", ville="Lyon", code_postal="69007",
                                     latitude=45.742, longitude=4.841)
    return Vendeur.objects.create(
        utilisateur=utilisateur, nom_boutique="TechSophie",
        type_activite=TypeService.STANDARD, adresse=adresse,
        statut_validation=StatutValidation.VALIDE,
    )


@pytest.fixture
def produit(boutique):
    return Produit.objects.create(
        vendeur=boutique, nom="Casque", prix_unitaire_centimes=18900, stock_disponible=5
    )


def entetes(cle=SESSION):
    return {"X-Panier-Session": cle}


# ── Sans compte ──────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_un_visiteur_remplit_son_panier_sans_compte(client, produit):
    reponse = client.post(
        reverse("ajouter-ligne"), {"produit": produit.id, "quantite": 2},
        content_type="application/json", headers=entetes(),
    )

    assert reponse.status_code == 201
    donnees = reponse.json()["data"]
    assert donnees["nombre_articles"] == 2
    assert donnees["total_centimes"] == 2 * 18900


@pytest.mark.django_db
def test_le_panier_est_retrouve_a_la_visite_suivante(client, produit):
    client.post(reverse("ajouter-ligne"), {"produit": produit.id},
                content_type="application/json", headers=entetes())

    reponse = client.get(reverse("voir-panier"), headers=entetes())

    assert reponse.json()["data"]["nombre_articles"] == 1


@pytest.mark.django_db
def test_une_autre_session_ne_voit_pas_le_panier(client, produit):
    client.post(reverse("ajouter-ligne"), {"produit": produit.id},
                content_type="application/json", headers=entetes())

    reponse = client.get(reverse("voir-panier"), headers=entetes("une-autre-session"))

    assert reponse.json()["data"]["nombre_articles"] == 0


@pytest.mark.django_db
def test_ajouter_deux_fois_le_meme_produit_cumule(client, produit):
    for _ in range(2):
        client.post(reverse("ajouter-ligne"), {"produit": produit.id, "quantite": 1},
                    content_type="application/json", headers=entetes())

    donnees = client.get(reverse("voir-panier"), headers=entetes()).json()["data"]
    assert len(donnees["lignes"]) == 1, "une seule ligne, pas deux"
    assert donnees["nombre_articles"] == 2


# ── Les gardes ───────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_on_ne_commande_pas_plus_que_le_stock(client, produit):
    reponse = client.post(
        reverse("ajouter-ligne"), {"produit": produit.id, "quantite": 99},
        content_type="application/json", headers=entetes(),
    )

    assert reponse.status_code == 409
    assert reponse.json()["erreur"]["code"] == "stock_insuffisant"


@pytest.mark.django_db
def test_un_produit_masque_n_entre_pas_au_panier(client, produit):
    produit.est_visible = False
    produit.save()

    reponse = client.post(
        reverse("ajouter-ligne"), {"produit": produit.id},
        content_type="application/json", headers=entetes(),
    )

    assert reponse.status_code == 404


@pytest.mark.django_db
def test_un_produit_de_vendeur_non_valide_n_entre_pas_au_panier(client, produit):
    produit.vendeur.statut_validation = StatutValidation.EN_ATTENTE
    produit.vendeur.save()

    reponse = client.post(
        reverse("ajouter-ligne"), {"produit": produit.id},
        content_type="application/json", headers=entetes(),
    )

    assert reponse.status_code == 404


# ── Le prix courant fait foi (R-05) ──────────────────────────────────────

@pytest.mark.django_db
def test_un_changement_de_prix_est_signale_et_applique(client, produit):
    client.post(reverse("ajouter-ligne"), {"produit": produit.id},
                content_type="application/json", headers=entetes())

    produit.prix_unitaire_centimes = 15900
    produit.save()

    ligne = client.get(reverse("voir-panier"), headers=entetes()).json()["data"]["lignes"][0]
    # Le panier affiche le prix COURANT, et previent que le prix a bouge.
    assert ligne["sous_total_centimes"] == 15900
    assert ligne["prix_a_change"] is True


# ── La fusion a la connexion, coeur de D-03 ──────────────────────────────

@pytest.mark.django_db
def test_le_panier_du_visiteur_suit_le_client_a_la_connexion(client, produit):
    compte = Utilisateur.objects.create_user(
        email="lea@exemple.fr", password=MOT_DE_PASSE, nom="Martin", prenom="Lea",
        role="CLIENT", statut_compte=StatutCompte.ACTIF,
    )
    Client.objects.create(utilisateur=compte)
    client.post(reverse("ajouter-ligne"), {"produit": produit.id, "quantite": 2},
                content_type="application/json", headers=entetes())

    connexion = client.post(
        reverse("connexion"), {"email": compte.email, "mot_de_passe": MOT_DE_PASSE},
        content_type="application/json", headers=entetes(),
    )
    jeton = connexion.json()["data"]["acces"]

    apres = client.get(reverse("voir-panier"), headers={"Authorization": f"Bearer {jeton}"})

    assert apres.json()["data"]["nombre_articles"] == 2, (
        "sans cette fusion, le visiteur retrouve son panier vide apres inscription"
    )
    # Le panier anonyme ne doit pas rester actif en double.
    assert Panier.objects.filter(cle_session=SESSION, statut=StatutPanier.ACTIF).count() == 0


@pytest.mark.django_db
def test_le_panier_signale_plusieurs_boutiques(client, produit, boutique):
    autre_utilisateur = Utilisateur.objects.create_user(
        email="karim@exemple.fr", password=MOT_DE_PASSE, nom="Benali", prenom="Karim",
        role="VENDEUR", statut_compte=StatutCompte.ACTIF,
    )
    autre = Vendeur.objects.create(
        utilisateur=autre_utilisateur, nom_boutique="Chez Karim",
        type_activite=TypeService.EXPRESS, statut_validation=StatutValidation.VALIDE,
    )
    plat = Produit.objects.create(
        vendeur=autre, nom="Ramen", prix_unitaire_centimes=1290, stock_disponible=10
    )

    for identifiant in (produit.id, plat.id):
        client.post(reverse("ajouter-ligne"), {"produit": identifiant},
                    content_type="application/json", headers=entetes())

    donnees = client.get(reverse("voir-panier"), headers=entetes()).json()["data"]
    # Deux boutiques donneront deux commandes (D-10) : le panier le dit avant
    # le paiement, pas apres.
    assert sorted(donnees["boutiques"]) == ["Chez Karim", "TechSophie"]
