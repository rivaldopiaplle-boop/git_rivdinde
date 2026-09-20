import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_sante_repond_et_voit_la_base(client):
    reponse = client.get(reverse("sante"))

    assert reponse.status_code == 200
    corps = reponse.json()
    assert corps["statut"] == "en ligne"
    assert corps["base_de_donnees"] == "connectee"


@pytest.mark.django_db
def test_sante_ne_fuit_aucun_secret(client, settings):
    # Un point de sante est public : il ne doit jamais renvoyer la chaine de
    # connexion, la cle secrete ni le nom de la machine.
    corps = client.get(reverse("sante")).content.decode()

    assert settings.SECRET_KEY not in corps
    assert "postgresql://" not in corps
