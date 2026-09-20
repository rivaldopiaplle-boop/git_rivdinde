from django.conf import settings
from django.db import connection
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

VERSION = "0.1.0"


@api_view(["GET"])
@permission_classes([AllowAny])
def sante(_requete):
    """Dit si l'API repond, et si elle voit sa base.

    Trois usages, tous prevus des la tranche 0 :
      - le front l'appelle au demarrage pour afficher "API en ligne" ;
      - l'hebergeur l'interroge pour savoir si le conteneur est vivant ;
      - la tache de reveil du jour de la demonstration tape ici (D-19).

    Volontairement public et sans donnee sensible : ni version de Django, ni
    chaine de connexion, ni nom de serveur.
    """
    base_ok = True
    try:
        with connection.cursor() as curseur:
            curseur.execute("SELECT 1")
            curseur.fetchone()
    except Exception:
        base_ok = False

    return Response(
        {
            "statut": "en ligne" if base_ok else "degrade",
            "version": VERSION,
            "base_de_donnees": "connectee" if base_ok else "injoignable",
            "environnement": "developpement" if settings.DEBUG else "production",
            "heure": timezone.now().isoformat(),
        },
        status=200 if base_ok else 503,
    )
