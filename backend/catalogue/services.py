"""Les regles du catalogue et du stock, hors des vues."""
from django.db import transaction

from .models import MouvementStock, PhotoProduit, TypeMouvement

PHOTOS_MAX = 6


class RegleMetier(Exception):
    """Une regle refuse l'operation. Le message est destine a l'utilisateur."""


@transaction.atomic
def ajouter_photo(produit, url, texte_alternatif=""):
    if produit.photos.count() >= PHOTOS_MAX:
        raise RegleMetier(f"Un produit ne peut pas avoir plus de {PHOTOS_MAX} photos.")

    ordre = (produit.photos.order_by("-ordre").values_list("ordre", flat=True).first() or 0) + 1
    photo = PhotoProduit.objects.create(
        produit=produit,
        url=url,
        ordre=ordre,
        # Ce que lit un lecteur d'ecran. Rempli automatiquement plutot que
        # laisse vide : une image sans description est invisible pour qui ne
        # voit pas l'ecran.
        texte_alternatif=texte_alternatif or f"{produit.nom} — {produit.vendeur.nom_boutique}",
    )
    _rafraichir_image_principale(produit)
    return photo


@transaction.atomic
def reordonner_photos(produit, identifiants):
    """La premiere de la liste devient la photo principale."""
    photos = {photo.id: photo for photo in produit.photos.all()}
    if set(identifiants) != set(photos):
        raise RegleMetier("La liste doit contenir exactement les photos du produit.")

    # Deux passes : la contrainte d'unicite (produit, ordre) interdit de
    # reordonner en une seule fois sans collision. On decale d'abord tout
    # au-dessus de la plage utilisee, puis on redescend aux valeurs finales.
    # (Vers le haut et non vers le negatif : `ordre` refuse les nombres
    # negatifs, et la base l'a rappele au premier essai.)
    DECALAGE = 1000
    for position, identifiant in enumerate(identifiants, start=1):
        photos[identifiant].ordre = DECALAGE + position
    PhotoProduit.objects.bulk_update(photos.values(), ["ordre"])

    for photo in photos.values():
        photo.ordre -= DECALAGE
    PhotoProduit.objects.bulk_update(photos.values(), ["ordre"])

    _rafraichir_image_principale(produit)


@transaction.atomic
def supprimer_photo_du_produit(produit, photo):
    photo.delete()
    for position, restante in enumerate(produit.photos.order_by("ordre"), start=1):
        if restante.ordre != position:
            restante.ordre = position
            restante.save(update_fields=["ordre"])
    _rafraichir_image_principale(produit)


def _rafraichir_image_principale(produit):
    """`image_principale_url` est une copie de la photo d'ordre 1.

    Denormalisation assumee : sans elle, afficher cinquante produits
    demanderait cinquante jointures (contrat-medias.md § 5).
    """
    premiere = produit.photos.order_by("ordre").first()
    nouvelle = premiere.url if premiere else ""
    if produit.image_principale_url != nouvelle:
        produit.image_principale_url = nouvelle
        produit.save(update_fields=["image_principale_url"])


@transaction.atomic
def ajuster_stock(produit, quantite, type_mouvement, motif, auteur):
    """Tout changement de stock laisse une trace (scenario 4.4).

    Un ajustement manuel sans motif est refuse : c'est la seule facon de
    retrouver plus tard pourquoi un chiffre a bouge — casse, inventaire,
    erreur de saisie.
    """
    if quantite == 0:
        raise RegleMetier("La quantite ne peut pas etre nulle.")
    if type_mouvement == TypeMouvement.AJUSTEMENT and not motif.strip():
        raise RegleMetier("Un ajustement manuel exige un motif.")

    nouveau = produit.stock_disponible + quantite
    if nouveau < 0:
        raise RegleMetier(
            f"Le stock ne peut pas devenir negatif : il est de {produit.stock_disponible}."
        )
    if nouveau < produit.stock_reserve:
        raise RegleMetier(
            f"{produit.stock_reserve} exemplaire(s) sont reserves par des paiements en cours."
        )

    produit.stock_disponible = nouveau
    produit.save(update_fields=["stock_disponible"])

    return MouvementStock.objects.create(
        produit=produit,
        auteur=auteur,
        type=type_mouvement,
        quantite=quantite,
        motif=motif.strip(),
        stock_apres=nouveau,
    )
