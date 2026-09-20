"""Ou vont les fichiers televerses — et comment ils sont nettoyes.

Une interface, deux implementations (D-18) : le disque local en developpement,
Cloudinary en ligne. Le reste du code ne sait pas laquelle repond.

Le traitement est le meme dans les deux cas, et il n'est pas negociable :
verifier que le fichier est bien une image, retirer les metadonnees, recadrer,
convertir. Une photo prise au telephone porte les coordonnees GPS de qui l'a
prise — les publier serait une fuite discrete et grave (contrat-medias.md § 3).
"""
import io
import os
import uuid

from django.conf import settings
from PIL import Image, UnidentifiedImageError

LARGEUR = 900
HAUTEUR = 675
TAILLE_MAX_OCTETS = 5 * 1024 * 1024
FORMATS_ACCEPTES = {"JPEG", "PNG", "WEBP"}


class FichierRefuse(Exception):
    """Le fichier n'est pas une image utilisable. Le message est pour l'humain."""


def _ouvrir_et_verifier(fichier):
    if fichier.size > TAILLE_MAX_OCTETS:
        millions = fichier.size / 1_048_576
        raise FichierRefuse(
            f"Cette image fait {millions:.1f} Mo, la limite est de 5 Mo."
        )

    try:
        image = Image.open(fichier)
        image.load()
    except (UnidentifiedImageError, OSError) as erreur:
        # On ne regarde jamais l'extension : renommer un script en .jpg est le
        # moyen le plus classique de faire televerser autre chose qu'une image.
        raise FichierRefuse("Ce fichier n'est pas une image lisible.") from erreur

    if image.format not in FORMATS_ACCEPTES:
        raise FichierRefuse("Formats acceptes : JPEG, PNG ou WebP.")
    if image.width < 600 or image.height < 600:
        raise FichierRefuse(
            f"Image trop petite ({image.width}x{image.height}). Minimum 600 x 600."
        )
    return image


def _preparer(image):
    """Recadre au format de la grille, puis reconstruit sans metadonnee."""
    image = image.convert("RGB")

    ratio = LARGEUR / HAUTEUR
    largeur, hauteur = image.size
    if largeur / hauteur > ratio:
        cible = int(hauteur * ratio)
        gauche = (largeur - cible) // 2
        image = image.crop((gauche, 0, gauche + cible, hauteur))
    else:
        cible = int(largeur / ratio)
        haut = (hauteur - cible) // 2
        image = image.crop((0, haut, largeur, haut + cible))

    image = image.resize((LARGEUR, HAUTEUR), Image.LANCZOS)

    # Reconstruite depuis ses seuls pixels, l'image ne porte plus ni EXIF ni GPS.
    propre = Image.new("RGB", image.size)
    propre.putdata(list(image.getdata()))
    return propre


def enregistrer_photo(fichier, dossier="produits"):
    """Verifie, nettoie et enregistre. Renvoie le chemin public de l'image."""
    image = _preparer(_ouvrir_et_verifier(fichier))

    nom = f"{uuid.uuid4().hex}.webp"
    if settings.CLOUDINARY_ACTIF:  # pragma: no cover - demande un compte
        import cloudinary.uploader

        tampon = io.BytesIO()
        image.save(tampon, "WEBP", quality=82, method=5)
        tampon.seek(0)
        try:
            resultat = cloudinary.uploader.upload(tampon, folder=dossier, resource_type="image")
        except Exception as erreur:
            # Une cle fausse ne doit pas produire un 500 illisible. On ne
            # bascule pas non plus en silence sur le disque local : en ligne,
            # ce disque est efface a chaque redeploiement (D-19), et la photo
            # disparaitrait sans que personne ne comprenne pourquoi.
            raise FichierRefuse(
                "Le stockage d'images est mal configure. Verifie CLOUDINARY_CLOUD_NAME, "
                "CLOUDINARY_API_KEY et CLOUDINARY_API_SECRET dans backend/.env — "
                f"le service a repondu : {erreur}"
            ) from erreur
        return resultat["secure_url"]

    chemin_dossier = os.path.join(settings.MEDIA_ROOT, dossier)
    os.makedirs(chemin_dossier, exist_ok=True)
    image.save(os.path.join(chemin_dossier, nom), "WEBP", quality=82, method=5)
    return f"{settings.MEDIA_URL}{dossier}/{nom}"


def supprimer_photo(chemin_public, dossier="produits"):
    """Une photo est un fichier, pas une donnee d'affaires : sa suppression est
    reelle (contrat-medias.md § 6)."""
    if not chemin_public or chemin_public.startswith("http"):
        return
    nom = os.path.basename(chemin_public)
    chemin = os.path.join(settings.MEDIA_ROOT, dossier, nom)
    if os.path.exists(chemin):
        os.remove(chemin)
