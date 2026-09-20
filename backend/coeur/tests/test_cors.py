"""Le contrat CORS, verrouille par des tests.

Ce fichier existe a cause d'un bug reel : l'en-tete `X-Panier-Session`, ajoute
a toutes les requetes du front, n'etait pas declare cote serveur. Le navigateur
bloquait donc chaque appel **avant de l'envoyer**, et le front n'affichait
qu'un « l'API ne repond pas » — alors que l'API repondait parfaitement.

Ni pytest ni un client en ligne de commande ne declenchent le controle CORS :
seul un navigateur le fait. D'ou ces tests, qui simulent ce qu'un navigateur
envoie avant chaque requete.
"""
import pytest
from django.urls import reverse

ORIGINE = "http://localhost:5173"


def preliminaire(client, chemin, entetes_demandes, methode="GET"):
    """La requete OPTIONS qu'un navigateur envoie avant une requete complexe."""
    return client.options(
        chemin,
        HTTP_ORIGIN=ORIGINE,
        HTTP_ACCESS_CONTROL_REQUEST_METHOD=methode,
        HTTP_ACCESS_CONTROL_REQUEST_HEADERS=entetes_demandes,
    )


@pytest.mark.django_db
def test_l_origine_du_front_est_autorisee(client):
    reponse = preliminaire(client, reverse("liste-produits"), "content-type")

    assert reponse.status_code == 200
    assert reponse["access-control-allow-origin"] == ORIGINE


@pytest.mark.django_db
def test_l_entete_de_session_de_panier_est_autorise(client):
    """Sans lui, le catalogue est vide et la connexion echoue (bloc H)."""
    reponse = preliminaire(client, reverse("liste-produits"), "content-type,x-panier-session")

    autorises = reponse["access-control-allow-headers"].lower()
    assert "x-panier-session" in autorises


@pytest.mark.django_db
def test_le_jeton_reste_autorise(client):
    reponse = preliminaire(client, reverse("moi"), "authorization")

    assert "authorization" in reponse["access-control-allow-headers"].lower()


@pytest.mark.django_db
def test_les_methodes_du_panier_sont_autorisees(client):
    reponse = preliminaire(client, reverse("ajouter-ligne"), "content-type", methode="POST")

    autorisees = reponse["access-control-allow-methods"]
    for methode in ("GET", "POST", "PATCH", "DELETE"):
        assert methode in autorisees


@pytest.mark.django_db
def test_une_origine_inconnue_n_est_pas_autorisee(client):
    reponse = client.options(
        reverse("liste-produits"),
        HTTP_ORIGIN="https://un-site-qui-n-est-pas-le-notre.example",
        HTTP_ACCESS_CONTROL_REQUEST_METHOD="GET",
    )

    # Le navigateur bloquera : aucune autorisation n'est renvoyee.
    assert reponse.get("access-control-allow-origin") is None
