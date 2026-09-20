"""Reglages communs a toute la suite de tests.

Le principe : **un test ne touche jamais le reseau**. Il doit passer dans un
train, dans une chaine d'integration sans secrets, et donner le meme resultat
a chaque execution.
"""
import pytest


@pytest.fixture(autouse=True)
def stockage_local(settings, tmp_path):
    """Force le disque local pour les images, meme si Cloudinary est configure.

    Sans cela, la suite echouait sur la machine de developpement des que des
    cles Cloudinary etaient presentes dans .env : les tests essayaient de
    televerser pour de vrai.
    """
    settings.CLOUDINARY_ACTIF = False
    settings.MEDIA_ROOT = tmp_path / "media"
    return settings
