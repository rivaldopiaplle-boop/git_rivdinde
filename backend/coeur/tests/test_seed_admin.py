import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command


@pytest.mark.django_db
def test_seed_admin_cree_un_superutilisateur():
    call_command("seed_admin", mot_de_passe="motdepasse-de-test")

    compte = get_user_model().objects.get(email="admin@rivdinde.local")
    assert compte.is_superuser and compte.is_staff and compte.is_active
    assert compte.check_password("motdepasse-de-test")


@pytest.mark.django_db
def test_seed_admin_est_idempotente():
    # La rejouer ne doit ni creer de doublon ni echouer : c'est ce qui permet
    # de la lancer a chaque deploiement sans y reflechir.
    call_command("seed_admin", mot_de_passe="premier")
    call_command("seed_admin", mot_de_passe="second")

    comptes = get_user_model().objects.filter(email="admin@rivdinde.local")
    assert comptes.count() == 1
    assert comptes.first().check_password("second")


@pytest.mark.django_db
def test_seed_admin_refuse_sans_mot_de_passe_hors_developpement(settings, monkeypatch):
    from django.core.management.base import CommandError

    settings.DEBUG = False
    monkeypatch.setenv("ADMIN_MOT_DE_PASSE", "")

    with pytest.raises(CommandError):
        call_command("seed_admin")


@pytest.mark.django_db
def test_seed_admin_ne_change_pas_le_mot_de_passe_dun_compte_existant(monkeypatch):
    # Sinon `demarrer.py`, qui l'appelle a chaque lancement, changerait le mot
    # de passe de l'admin toutes les cinq minutes.
    call_command("seed_admin", mot_de_passe="celui-que-je-connais")
    monkeypatch.setenv("ADMIN_MOT_DE_PASSE", "")

    call_command("seed_admin")

    compte = get_user_model().objects.get(email="admin@rivdinde.local")
    assert compte.check_password("celui-que-je-connais")
