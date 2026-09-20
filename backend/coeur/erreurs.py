"""Un format d'erreur unique pour toute l'API.

Sans ce gestionnaire, DRF renvoie tantot {"detail": "..."}, tantot
{"champ": ["..."]}, tantot une liste. Le front devrait alors deviner la forme
a chaque appel — et c'est ainsi qu'on finit par afficher « [object Object] »
a un utilisateur.

Format retenu, identique pour toutes les erreurs :

    {"erreur": {"code": "validation", "message": "…", "details": {…}}}
"""
from rest_framework.views import exception_handler

CODES = {
    400: "validation",
    401: "non_authentifie",
    403: "non_autorise",
    404: "introuvable",
    405: "methode_non_autorisee",
    409: "conflit",
    429: "trop_de_requetes",
}


def gestionnaire_erreurs(exception, contexte):
    reponse = exception_handler(exception, contexte)
    if reponse is None:
        # Erreur non prevue : on laisse Django la traiter, pour ne pas masquer
        # une trace utile derriere un joli JSON.
        return None

    details = reponse.data
    message = None
    if isinstance(details, dict) and "detail" in details:
        message = str(details["detail"])
        details = {}
    elif isinstance(details, dict):
        premier = next(iter(details.values()), None)
        if isinstance(premier, list) and premier:
            message = str(premier[0])
    elif isinstance(details, list) and details:
        message = str(details[0])
        details = {}

    reponse.data = {
        "erreur": {
            "code": CODES.get(reponse.status_code, "erreur"),
            "message": message or "La requete n'a pas pu etre traitee.",
            "details": details if isinstance(details, dict) else {},
        }
    }
    return reponse
