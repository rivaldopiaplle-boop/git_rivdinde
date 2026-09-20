# ─────────────────────────────────────────────────────────────────────────
#  RivDinde — configuration Django
#
#  Un seul fichier de configuration, pilote par des variables
#  d'environnement (voir .env.example). Pas de settings/dev.py et
#  settings/prod.py : deux fichiers qui divergent finissent par se
#  contredire, et l'ecart ne se voit que le jour du deploiement.
# ─────────────────────────────────────────────────────────────────────────
import os
import secrets
from datetime import timedelta
from pathlib import Path

import dj_database_url
from corsheaders.defaults import default_headers
from dotenv import load_dotenv

RACINE = Path(__file__).resolve().parent.parent
load_dotenv(RACINE / ".env")


def env(nom, defaut=""):
    return os.environ.get(nom, defaut).strip()


def env_bool(nom, defaut=False):
    valeur = env(nom).lower()
    if not valeur:
        return defaut
    return valeur in ("1", "true", "oui", "yes", "on")


def env_liste(nom, defaut=""):
    brut = env(nom) or defaut
    return [x.strip() for x in brut.split(",") if x.strip()]


DEBUG = env_bool("DEBUG", True)

# En developpement, une cle jetable est generee a chaque demarrage : rien a
# configurer pour commencer. En ligne, l'absence de cle est une erreur
# franche plutot qu'une faiblesse silencieuse.
SECRET_KEY = env("DJANGO_SECRET_KEY")
if not SECRET_KEY:
    if not DEBUG:
        raise RuntimeError(
            "DJANGO_SECRET_KEY est obligatoire hors developpement. "
            'Generer : python -c "import secrets; print(secrets.token_urlsafe(50))"'
        )
    SECRET_KEY = "dev-" + secrets.token_urlsafe(32)

ALLOWED_HOSTS = env_liste("ALLOWED_HOSTS", "localhost,127.0.0.1")

# Render publie le domaine du service dans cette variable. Sans cette ligne,
# la premiere mise en ligne repond 400 sans expliquer pourquoi.
hote_render = env("RENDER_EXTERNAL_HOSTNAME")
if hote_render:
    ALLOWED_HOSTS.append(hote_render)


# ── Applications ─────────────────────────────────────────────────────────

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt",
    "corsheaders",
    # Une app par zone du modele de donnees. Le decoupage suit le MCD, pas la
    # technique : on trouve un modele la ou on le cherche.
    "coeur",
    "comptes",
    "catalogue",
    "commandes",
    "paiements",
    "livraisons",
    "engagement",
]

# L'authentification passe par notre propre modele : e-mail unique comme
# identifiant, role et statut de compte portes par l'utilisateur lui-meme.
# Changer cette valeur apres la premiere migration est tres couteux — c'est
# pour cela qu'elle est posee des la tranche 1.
AUTH_USER_MODEL = "comptes.Utilisateur"

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]


# ── Base de donnees ──────────────────────────────────────────────────────

DATABASES = {
    "default": dj_database_url.parse(
        env("DATABASE_URL", "postgresql://rivdinde:rivdinde@localhost:5433/rivdinde"),
        conn_max_age=600,
        conn_health_checks=True,
    )
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# ── Mots de passe ────────────────────────────────────────────────────────
#
# Sans cette liste, Django accepte « 1234 ». Ce n'est pas un reglage de
# confort : c'est la seule chose qui separe un compte d'un compte ouvert.
# Un test le verifie (comptes/tests/test_inscription_et_validation.py).

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 10},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# ── API ──────────────────────────────────────────────────────────────────

REST_FRAMEWORK = {
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "EXCEPTION_HANDLER": "coeur.erreurs.gestionnaire_erreurs",
}

# Jetons JWT. Duree courte pour l'acces, longue pour le rafraichissement :
# un jeton vole ne sert que quelques minutes, et l'utilisateur ne se
# reconnecte pas toutes les heures.
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=14),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": False,
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "id_utilisateur",
}

CORS_ALLOWED_ORIGINS = env_liste(
    "CORS_ORIGINS", "http://localhost:5173,http://localhost:8100"
)

# Tout en-tete personnalise doit etre declare ici, sinon le navigateur bloque
# la requete AVANT de l'envoyer — et le front ne recoit qu'une erreur reseau
# sans explication. Ni pytest ni un client en ligne de commande ne declenchent
# ce controle : seul un navigateur le fait. C'est ainsi que le catalogue s'est
# retrouve vide alors que l'API repondait parfaitement.
CORS_ALLOW_HEADERS = (
    *default_headers,
    # La cle qui identifie le panier d'un visiteur sans compte (D-34).
    "x-panier-session",
)


# ── Langue, heure, fichiers ──────────────────────────────────────────────
#
# Les dates sont stockees en UTC et converties a l'affichage : une commande
# passee a 23 h 30 ne doit pas changer de jour selon qui la regarde.

LANGUAGE_CODE = "fr-fr"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = RACINE / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

if DEBUG:
    # En developpement, collectstatic n a pas tourne et staticfiles/ n existe
    # pas : WhiteNoise avertirait a chaque requete. Il sert alors les fichiers
    # depuis leurs dossiers d origine, comme le fait runserver.
    WHITENOISE_USE_FINDERS = True
    WHITENOISE_AUTOREFRESH = True

MEDIA_URL = "/media/"
MEDIA_ROOT = RACINE / "media"

# Les images televersees. Sans configuration, elles vont sur le disque local et
# tout fonctionne (D-18). En ligne, Cloudinary est OBLIGATOIRE : le disque du
# conteneur est efface a chaque redeploiement (D-19).
CLOUDINARY_ACTIF = bool(env("CLOUDINARY_CLOUD_NAME") and env("CLOUDINARY_API_KEY"))
if CLOUDINARY_ACTIF:  # pragma: no cover - demande un compte
    import cloudinary

    cloudinary.config(
        cloud_name=env("CLOUDINARY_CLOUD_NAME"),
        api_key=env("CLOUDINARY_API_KEY"),
        api_secret=env("CLOUDINARY_API_SECRET"),
        secure=True,
    )


# ── Courriels ────────────────────────────────────────────────────────────

if env("SMTP_HOST"):
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_HOST = env("SMTP_HOST")
    EMAIL_PORT = int(env("SMTP_PORT", "1025"))
    EMAIL_HOST_USER = env("SMTP_USER")
    EMAIL_HOST_PASSWORD = env("SMTP_PASS")
else:
    # Aucun SMTP configure : les courriels s'affichent dans la console.
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

DEFAULT_FROM_EMAIL = env("MAIL_EXPEDITEUR", "RivDinde <ne-pas-repondre@rivdinde.local>")


# ── Securite en ligne ────────────────────────────────────────────────────

if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 60 * 60 * 24 * 30
