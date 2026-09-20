"""Le decoupage du panier en commandes — decision D-10.

C'est la piece la plus structurante du projet : un panier mixte donne une
commande par boutique Express, plus une seule commande Standard multi-vendeur.
Ces tests sont la pour que cette regle ne derive jamais.
"""
import pytest
from django.urls import reverse

from catalogue.models import Produit
from commandes.models import Commande, LigneCommande, SousCommande
from comptes.models import (
    Adresse,
    AdresseClient,
    Client,
    StatutCompte,
    StatutValidation,
    TypeService,
    Utilisateur,
    Vendeur,
)

MOT_DE_PASSE = "UnMotDePasseSolide!2026"
SESSION = "session-decoupage"


def creer_vendeur(nom, service, commission=0.15):
    utilisateur = Utilisateur.objects.create_user(
        email=f"{nom.lower().replace(' ', '')}@exemple.fr", password=MOT_DE_PASSE,
        nom=nom, prenom="Test", role="VENDEUR", statut_compte=StatutCompte.ACTIF,
    )
    return Vendeur.objects.create(
        utilisateur=utilisateur, nom_boutique=nom, type_activite=service,
        statut_validation=StatutValidation.VALIDE, taux_commission=commission,
    )


def creer_produit(vendeur, nom, prix=1000, stock=20):
    return Produit.objects.create(
        vendeur=vendeur, nom=nom, prix_unitaire_centimes=prix, stock_disponible=stock
    )


@pytest.fixture
def lea(db):
    compte = Utilisateur.objects.create_user(
        email="lea@exemple.fr", password=MOT_DE_PASSE, nom="Martin", prenom="Lea",
        role="CLIENT", statut_compte=StatutCompte.ACTIF,
    )
    profil = Client.objects.create(utilisateur=compte)
    adresse = Adresse.objects.create(rue="8 rue Victor Hugo", ville="Lyon", code_postal="69002")
    AdresseClient.objects.create(client=profil, adresse=adresse, est_principale=True)
    return profil


@pytest.fixture
def boutiques(db):
    return {
        "karim": creer_vendeur("Chez Karim", TypeService.EXPRESS),
        "amel": creer_vendeur("Chez Amel", TypeService.EXPRESS),
        "sophie": creer_vendeur("TechSophie", TypeService.STANDARD),
        "leo": creer_vendeur("LivresLeo", TypeService.STANDARD),
    }


def remplir(client, produits, entetes=None):
    for produit in produits:
        client.post(
            reverse("ajouter-ligne"), {"produit": produit.id, "quantite": 1},
            content_type="application/json", headers=entetes or {"X-Panier-Session": SESSION},
        )


def connecter(client, email=" lea@exemple.fr"):
    reponse = client.post(
        reverse("connexion"), {"email": email.strip(), "mot_de_passe": MOT_DE_PASSE},
        content_type="application/json", headers={"X-Panier-Session": SESSION},
    )
    return {"Authorization": f"Bearer {reponse.json()['data']['acces']}"}


# ── La regle du decoupage ────────────────────────────────────────────────

@pytest.mark.django_db
def test_un_panier_mixte_donne_une_commande_par_express_plus_une_standard(client, lea, boutiques):
    """Le cas du bloc A-17, verifie de bout en bout."""
    remplir(client, [
        creer_produit(boutiques["karim"], "Ramen", 1290),
        creer_produit(boutiques["amel"], "Pizza", 1350),
        creer_produit(boutiques["sophie"], "Casque", 18900),
        creer_produit(boutiques["leo"], "Roman", 1800),
    ])
    entetes = connecter(client)

    reponse = client.post(reverse("creer-commandes"), {}, content_type="application/json",
                          headers=entetes)

    assert reponse.status_code == 201
    commandes = reponse.json()["data"]
    assert len(commandes) == 3, "deux Express distinctes, plus une seule Standard"

    express = [c for c in commandes if c["type_service"] == "EXPRESS"]
    standard = [c for c in commandes if c["type_service"] == "STANDARD"]
    assert len(express) == 2
    assert all(len(c["boutiques"]) == 1 for c in express), "un seul vendeur par commande Express"
    assert len(standard) == 1, "les vendeurs Standard sont regroupes en UNE commande"
    assert sorted(standard[0]["boutiques"]) == ["LivresLeo", "TechSophie"]


@pytest.mark.django_db
def test_la_commande_standard_se_decompose_en_sous_commandes_par_vendeur(client, lea, boutiques):
    remplir(client, [
        creer_produit(boutiques["sophie"], "Casque", 18900),
        creer_produit(boutiques["leo"], "Roman", 1800),
    ])

    client.post(reverse("creer-commandes"), {}, content_type="application/json",
                headers=connecter(client))

    commande = Commande.objects.get(type_service=TypeService.STANDARD)
    assert commande.sous_commandes.count() == 2, "chaque vendeur voit sa part, et rien d'autre"


@pytest.mark.django_db
def test_une_commande_express_a_exactement_une_sous_commande(client, lea, boutiques):
    remplir(client, [creer_produit(boutiques["karim"], "Ramen", 1290)])

    client.post(reverse("creer-commandes"), {}, content_type="application/json",
                headers=connecter(client))

    commande = Commande.objects.get(type_service=TypeService.EXPRESS)
    # Une seule sous-commande, ce qui permet d'ecrire un seul code de
    # preparation pour les deux modes de service.
    assert commande.sous_commandes.count() == 1


# ── L'argent ─────────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_la_part_du_vendeur_et_la_commission_tombent_juste(client, lea, boutiques):
    remplir(client, [creer_produit(boutiques["karim"], "Ramen", 1000)])

    client.post(reverse("creer-commandes"), {}, content_type="application/json",
                headers=connecter(client))

    sous = SousCommande.objects.get()
    assert sous.montant_commission_centimes == 150, "15 % de commission"
    assert sous.montant_vendeur_centimes == 850
    assert sous.montant_vendeur_centimes + sous.montant_commission_centimes == 1000


@pytest.mark.django_db
def test_le_nom_et_le_prix_sont_recopies_dans_la_commande(client, lea, boutiques):
    produit = creer_produit(boutiques["karim"], "Ramen", 1290)
    remplir(client, [produit])
    client.post(reverse("creer-commandes"), {}, content_type="application/json",
                headers=connecter(client))

    produit.nom = "Ramen — nouvelle recette"
    produit.prix_unitaire_centimes = 1590
    produit.save()

    ligne = LigneCommande.objects.get()
    # Une commande passee ne change jamais : c'est la difference entre une
    # facture et un rapport.
    assert ligne.nom_produit_capture == "Ramen"
    assert ligne.prix_unitaire_centimes == 1290


@pytest.mark.django_db
def test_le_stock_est_reserve_et_non_decremente(client, lea, boutiques):
    produit = creer_produit(boutiques["karim"], "Ramen", 1290, stock=10)
    remplir(client, [produit])

    client.post(reverse("creer-commandes"), {}, content_type="application/json",
                headers=connecter(client))

    produit.refresh_from_db()
    # Le stock n'est pas encore vendu : il est mis de cote le temps du
    # paiement (D-15).
    assert produit.stock_disponible == 10
    assert produit.stock_reserve == 1
    assert produit.stock_commandable == 9


# ── Les gardes ───────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_un_panier_vide_ne_produit_aucune_commande(client, lea):
    reponse = client.post(reverse("creer-commandes"), {}, content_type="application/json",
                          headers=connecter(client))

    assert reponse.status_code == 409
    assert not Commande.objects.exists()


@pytest.mark.django_db
def test_un_produit_devenu_indisponible_bloque_toute_la_commande(client, lea, boutiques):
    disponible = creer_produit(boutiques["karim"], "Ramen", 1290)
    epuise = creer_produit(boutiques["sophie"], "Casque", 18900, stock=5)
    remplir(client, [disponible, epuise])
    epuise.stock_disponible = 0
    epuise.save()

    reponse = client.post(reverse("creer-commandes"), {}, content_type="application/json",
                          headers=connecter(client))

    assert reponse.status_code == 409
    # Tout ou rien : creer deux commandes sur trois puis echouer laisserait un
    # panier a moitie converti que personne ne saurait rattraper.
    assert not Commande.objects.exists()


@pytest.mark.django_db
def test_un_visiteur_sans_compte_ne_peut_pas_commander(client, boutiques):
    remplir(client, [creer_produit(boutiques["karim"], "Ramen", 1290)])

    reponse = client.post(reverse("creer-commandes"), {}, content_type="application/json",
                          headers={"X-Panier-Session": SESSION})

    # On regarde et on remplit son panier sans compte ; on ne commande pas
    # sans (D-03).
    assert reponse.status_code == 401


@pytest.mark.django_db
def test_le_panier_est_marque_converti(client, lea, boutiques):
    remplir(client, [creer_produit(boutiques["karim"], "Ramen", 1290)])
    entetes = connecter(client)

    client.post(reverse("creer-commandes"), {}, content_type="application/json", headers=entetes)

    apres = client.get(reverse("voir-panier"), headers=entetes).json()["data"]
    assert apres["nombre_articles"] == 0, "le panier converti ne reste pas actif"


# ── L'apercu, avant tout engagement ──────────────────────────────────────

@pytest.mark.django_db
def test_l_apercu_annonce_le_decoupage_avant_de_valider(client, boutiques):
    remplir(client, [
        creer_produit(boutiques["karim"], "Ramen", 1290),
        creer_produit(boutiques["sophie"], "Casque", 18900),
    ])

    donnees = client.get(reverse("apercu-commandes"),
                         headers={"X-Panier-Session": SESSION}).json()["data"]

    assert len(donnees["commandes"]) == 2
    assert donnees["total_centimes"] > 0
    # Le client sait qu'il cree deux commandes AVANT de payer.
    assert {c["type_service"] for c in donnees["commandes"]} == {"EXPRESS", "STANDARD"}


# ── La preparation, cote vendeur ─────────────────────────────────────────

@pytest.mark.django_db
def test_le_vendeur_fait_avancer_sa_part_dun_cran_a_la_fois(client, lea, boutiques):
    remplir(client, [creer_produit(boutiques["karim"], "Ramen", 1290)])
    client.post(reverse("creer-commandes"), {}, content_type="application/json",
                headers=connecter(client))
    sous = SousCommande.objects.get()
    entetes = connecter(client, "chezkarim@exemple.fr")

    saut = client.patch(
        reverse("avancer-preparation", args=[sous.id]), {"statut": "EXPEDIEE"},
        content_type="application/json", headers=entetes,
    )
    assert saut.status_code == 409, "on ne saute pas deux etapes"

    cran = client.patch(
        reverse("avancer-preparation", args=[sous.id]), {"statut": "EN_PREPARATION"},
        content_type="application/json", headers=entetes,
    )
    assert cran.status_code == 200
    assert cran.json()["data"]["suites_possibles"] == ["PRETE", "ANNULEE"]


@pytest.mark.django_db
def test_un_vendeur_ne_voit_que_sa_part_dune_commande_multi_vendeur(client, lea, boutiques):
    remplir(client, [
        creer_produit(boutiques["sophie"], "Casque", 18900),
        creer_produit(boutiques["leo"], "Roman", 1800),
    ])
    client.post(reverse("creer-commandes"), {}, content_type="application/json",
                headers=connecter(client))

    recues = client.get(reverse("commandes-recues"),
                        headers=connecter(client, "techsophie@exemple.fr")).json()["data"]

    assert len(recues) == 1
    assert recues[0]["boutique"] == "TechSophie"
    assert all(ligne["nom_produit_capture"] == "Casque" for ligne in recues[0]["lignes"])
