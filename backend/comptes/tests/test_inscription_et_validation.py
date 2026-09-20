"""Le test de sortie de la tranche 1, ecrit noir sur blanc.

« Un client s'inscrit et se connecte ; un vendeur cree reste bloque tant que
l'admin ne valide pas, et un test automatise le prouve. »
"""
import pytest
from django.urls import reverse

from comptes.models import Role, StatutCompte, StatutValidation, Utilisateur, Vendeur

MOT_DE_PASSE = "UnMotDePasseSolide!2026"


def inscrire_client(client_api, email="lea@exemple.fr"):
    return client_api.post(
        reverse("inscription-client"),
        {"email": email, "mot_de_passe": MOT_DE_PASSE, "nom": "Martin", "prenom": "Lea"},
        content_type="application/json",
    )


def inscrire_vendeur(client_api, email="karim@exemple.fr"):
    return client_api.post(
        reverse("inscription-vendeur"),
        {
            "email": email, "mot_de_passe": MOT_DE_PASSE, "nom": "Benali", "prenom": "Karim",
            "nom_boutique": "Chez Karim", "type_activite": "EXPRESS",
        },
        content_type="application/json",
    )


def connecter(client_api, email):
    return client_api.post(
        reverse("connexion"),
        {"email": email, "mot_de_passe": MOT_DE_PASSE},
        content_type="application/json",
    )


# ── Client ───────────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_un_client_s_inscrit_et_est_actif_immediatement(client):
    reponse = inscrire_client(client)

    assert reponse.status_code == 201
    donnees = reponse.json()["data"]
    assert donnees["utilisateur"]["role"] == Role.CLIENT
    assert donnees["utilisateur"]["statut_compte"] == StatutCompte.ACTIF
    assert donnees["acces"] and donnees["rafraichissement"]


@pytest.mark.django_db
def test_un_client_se_connecte_et_lit_son_profil(client):
    inscrire_client(client)

    reponse = connecter(client, "lea@exemple.fr")
    assert reponse.status_code == 200
    jeton = reponse.json()["data"]["acces"]

    moi = client.get(reverse("moi"), headers={"Authorization": f"Bearer {jeton}"})
    assert moi.status_code == 200
    assert moi.json()["data"]["utilisateur"]["prenom"] == "Lea"


@pytest.mark.django_db
def test_le_mot_de_passe_n_est_jamais_renvoye(client):
    corps = inscrire_client(client).content.decode()

    assert MOT_DE_PASSE not in corps
    assert "mot_de_passe" not in corps


@pytest.mark.django_db
def test_deux_comptes_ne_peuvent_pas_partager_une_adresse(client):
    inscrire_client(client)

    reponse = inscrire_client(client)

    assert reponse.status_code == 400
    assert reponse.json()["erreur"]["code"] == "validation"


@pytest.mark.django_db
def test_un_mot_de_passe_trop_faible_est_refuse(client):
    reponse = client.post(
        reverse("inscription-client"),
        {"email": "faible@exemple.fr", "mot_de_passe": "1234", "nom": "X", "prenom": "Y"},
        content_type="application/json",
    )

    assert reponse.status_code == 400


@pytest.mark.django_db
def test_identifiants_faux_ne_disent_pas_lequel(client):
    inscrire_client(client)

    reponse = client.post(
        reverse("connexion"),
        {"email": "lea@exemple.fr", "mot_de_passe": "mauvais"},
        content_type="application/json",
    )

    assert reponse.status_code == 401
    # Le message est le meme que pour un e-mail inconnu : sinon on peut
    # enumerer les comptes existants.
    assert reponse.json()["erreur"]["message"] == "E-mail ou mot de passe incorrect."


# ── Vendeur : le coeur du test de sortie ─────────────────────────────────

@pytest.mark.django_db
def test_un_vendeur_inscrit_reste_en_attente(client):
    reponse = inscrire_vendeur(client)

    assert reponse.status_code == 201
    assert reponse.json()["data"]["utilisateur"]["statut_compte"] == StatutCompte.EN_ATTENTE
    assert Vendeur.objects.get().statut_validation == StatutValidation.EN_ATTENTE


@pytest.mark.django_db
def test_un_vendeur_en_attente_se_connecte_mais_ne_peut_rien_faire(client):
    inscrire_vendeur(client)

    connexion = connecter(client, "karim@exemple.fr")
    assert connexion.status_code == 200, "il doit pouvoir voir son ecran d'attente"

    jeton = connexion.json()["data"]["acces"]
    refus = client.post(
        reverse("creer-gestionnaire"),
        {"email": "nadia@exemple.fr", "mot_de_passe": MOT_DE_PASSE, "nom": "N", "prenom": "Nadia"},
        content_type="application/json",
        headers={"Authorization": f"Bearer {jeton}"},
    )
    assert refus.status_code == 403, "tant qu'il n'est pas valide, aucune action metier"


@pytest.mark.django_db
def test_l_admin_valide_le_vendeur_qui_devient_alors_actif(client, django_user_model):
    inscrire_vendeur(client)
    admin = django_user_model.objects.create_user(
        email="fatou@rivdinde.local", password=MOT_DE_PASSE,
        nom="Diallo", prenom="Fatou", role=Role.ADMIN, statut_compte=StatutCompte.ACTIF,
    )
    jeton_admin = connecter(client, admin.email).json()["data"]["acces"]
    entete = {"Authorization": f"Bearer {jeton_admin}"}

    attente = client.get(reverse("validations"), headers=entete)
    assert len(attente.json()["data"]["vendeurs"]) == 1

    vendeur = Vendeur.objects.get()
    validation = client.post(reverse("valider-vendeur", args=[vendeur.id]), headers=entete)

    assert validation.status_code == 200
    vendeur.refresh_from_db()
    vendeur.utilisateur.refresh_from_db()
    assert vendeur.statut_validation == StatutValidation.VALIDE
    assert vendeur.utilisateur.statut_compte == StatutCompte.ACTIF


@pytest.mark.django_db
def test_un_vendeur_valide_cree_son_personnel(client):
    inscrire_vendeur(client)
    vendeur = Vendeur.objects.get()
    vendeur.statut_validation = StatutValidation.VALIDE
    vendeur.save()
    vendeur.utilisateur.statut_compte = StatutCompte.ACTIF
    vendeur.utilisateur.save()

    jeton = connecter(client, "karim@exemple.fr").json()["data"]["acces"]
    reponse = client.post(
        reverse("creer-gestionnaire"),
        {"email": "nadia@exemple.fr", "mot_de_passe": MOT_DE_PASSE,
         "nom": "Sow", "prenom": "Nadia"},
        content_type="application/json",
        headers={"Authorization": f"Bearer {jeton}"},
    )

    assert reponse.status_code == 201
    nadia = Utilisateur.objects.get(email="nadia@exemple.fr")
    assert nadia.role == Role.GESTIONNAIRE
    # Le rattachement vient du jeton, jamais de la charge utile : un vendeur
    # ne peut pas creer du personnel chez un concurrent.
    assert nadia.profil_gestionnaire.vendeur_id == vendeur.id


# ── Cloisonnement des roles ──────────────────────────────────────────────

@pytest.mark.django_db
def test_un_client_ne_peut_pas_atteindre_les_routes_admin(client):
    inscrire_client(client)
    jeton = connecter(client, "lea@exemple.fr").json()["data"]["acces"]

    reponse = client.get(reverse("validations"), headers={"Authorization": f"Bearer {jeton}"})

    assert reponse.status_code == 403
    assert reponse.json()["erreur"]["code"] == "non_autorise"


@pytest.mark.django_db
def test_sans_jeton_les_routes_protegees_repondent_401(client):
    reponse = client.get(reverse("moi"))

    assert reponse.status_code == 401
    assert reponse.json()["erreur"]["code"] == "non_authentifie"


@pytest.mark.django_db
def test_un_compte_suspendu_ne_se_connecte_plus(client):
    inscrire_client(client)
    utilisateur = Utilisateur.objects.get(email="lea@exemple.fr")
    utilisateur.statut_compte = StatutCompte.SUSPENDU
    utilisateur.save()

    reponse = connecter(client, "lea@exemple.fr")

    assert reponse.status_code == 403
    assert reponse.json()["erreur"]["code"] == "compte_bloque"
