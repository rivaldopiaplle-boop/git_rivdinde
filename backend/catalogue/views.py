"""Le catalogue : public en lecture, reserve au vendeur en ecriture.

Le point le plus structurant est le filtrage geographique (D-09) : les
produits d'un vendeur EXPRESS hors de son rayon de livraison ne sont pas
renvoyes du tout. Ce n'est pas un tri, c'est une absence — c'est ce qui rend
structurellement impossible une commande Express longue distance.
"""
from django.db.models import Count, Q
from rest_framework import status
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from coeur.geographie import distance_km
from coeur.stockage import FichierRefuse, enregistrer_photo, supprimer_photo
from comptes.models import StatutValidation, TypeService, Vendeur
from comptes.permissions import EstVendeur, EstVendeurOuSonPersonnel

from .models import Categorie, PhotoProduit, Produit, TypeMouvement
from .serializers import (
    BoutiqueSerializer,
    CategorieSerializer,
    MouvementStockSerializer,
    PhotoProduitSerializer,
    ProduitDetailSerializer,
    ProduitEcritureSerializer,
    ProduitListeSerializer,
)
from .services import (
    RegleMetier,
    ajouter_photo,
    ajuster_stock,
    reordonner_photos,
    supprimer_photo_du_produit,
)


def _position(requete):
    """La position du visiteur, si elle est connue. Sinon (None, None)."""
    try:
        return float(requete.query_params["lat"]), float(requete.query_params["lon"])
    except (KeyError, TypeError, ValueError):
        return None, None


def _visibles():
    """Le catalogue public : produits visibles de vendeurs valides.

    Un vendeur non valide n'a aucun produit au catalogue (R-07), et un produit
    masque par son vendeur disparait sans etre supprime (D-13).
    """
    return (
        Produit.objects.select_related("vendeur", "vendeur__adresse", "categorie")
        .filter(est_visible=True, vendeur__statut_validation=StatutValidation.VALIDE)
    )


def _filtrer_par_rayon(produits, lat, lon):
    """Retire les produits Express hors du rayon, et calcule les distances.

    Sans position connue, les boutiques Express sont ecartees du resultat
    plutot que montrees a tort : mieux vaut un catalogue Standard complet
    qu'un restaurant a trois cents kilometres (D-22).
    """
    gardes, distances = [], {}

    for produit in produits:
        vendeur = produit.vendeur
        if vendeur.type_activite != TypeService.EXPRESS:
            gardes.append(produit)
            continue

        adresse = vendeur.adresse
        if lat is None or adresse is None:
            continue

        d = distance_km(lat, lon, adresse.latitude, adresse.longitude)
        if d is None or d > float(vendeur.rayon_livraison_km):
            continue

        distances[produit.id] = d
        gardes.append(produit)

    return gardes, distances


@api_view(["GET"])
@permission_classes([AllowAny])
def liste_produits(requete):
    """Le catalogue, avec ses facettes.

    Les compteurs de categories et de boutiques sont calcules **sur le
    resultat reellement filtre**, jamais sur la base entiere. Sinon on affiche
    « Plats 4 » a un visiteur parisien qui, lui, ne voit aucun plat : les
    boutiques Express lyonnaises sont hors de son rayon.
    """
    produits = _visibles()

    if service := requete.query_params.get("type_service"):
        produits = produits.filter(vendeur__type_activite=service)
    if recherche := requete.query_params.get("recherche"):
        produits = produits.filter(
            Q(nom__icontains=recherche) | Q(description__icontains=recherche)
        )
    if requete.query_params.get("disponible") == "1":
        produits = produits.filter(stock_disponible__gt=0)

    lat, lon = _position(requete)
    base, distances = _filtrer_par_rayon(list(produits[:400]), lat, lon)

    # Les facettes decrivent CE QUI RESTE apres le filtrage geographique et la
    # recherche, mais avant les filtres de categorie et de boutique — sinon
    # cliquer sur une categorie ferait disparaitre toutes les autres.
    facettes = _facettes(base)

    categorie = requete.query_params.get("categorie")
    boutique = requete.query_params.get("boutique")
    resultat = [
        produit for produit in base
        if (not categorie or (produit.categorie and produit.categorie.slug == categorie))
        and (not boutique or str(produit.vendeur_id) == str(boutique))
    ]

    serializer = ProduitListeSerializer(
        resultat, many=True, context={"request": requete, "distances": distances}
    )
    return Response({
        "data": serializer.data,
        "meta": {"total": len(resultat), "total_avant_filtres": len(base), "facettes": facettes},
    })


def _facettes(produits):
    """Compte par categorie et par boutique, groupe par univers.

    Le regroupement par univers repond a une remarque simple : sept categories
    a plat ne disent rien, alors que « Restauration » et « High-tech » se
    lisent d'un coup d'oeil.
    """
    par_categorie = {}
    par_boutique = {}

    for produit in produits:
        if produit.categorie:
            cle = produit.categorie.slug
            entree = par_categorie.setdefault(cle, {
                "slug": cle,
                "nom": produit.categorie.nom,
                "univers": (produit.categorie.parente.nom if produit.categorie.parente
                            else "Autres"),
                "nombre": 0,
            })
            entree["nombre"] += 1

        vendeur = produit.vendeur
        entree = par_boutique.setdefault(vendeur.id, {
            "id": vendeur.id,
            "nom": vendeur.nom_boutique,
            "type_service": vendeur.type_activite,
            "nombre": 0,
        })
        entree["nombre"] += 1

    univers = {}
    for categorie in par_categorie.values():
        univers.setdefault(categorie["univers"], []).append(categorie)

    return {
        "univers": [
            {
                "nom": nom,
                "nombre": sum(c["nombre"] for c in categories),
                "categories": sorted(categories, key=lambda c: -c["nombre"]),
            }
            for nom, categories in sorted(univers.items())
        ],
        "boutiques": sorted(par_boutique.values(), key=lambda b: -b["nombre"]),
    }


@api_view(["GET"])
@permission_classes([AllowAny])
def detail_produit(requete, identifiant):
    try:
        produit = _visibles().prefetch_related("photos").get(pk=identifiant)
    except Produit.DoesNotExist:
        return Response(
            {"erreur": {"code": "introuvable", "message": "Ce produit n'existe pas ou n'est "
                                                          "plus au catalogue.", "details": {}}},
            status=status.HTTP_404_NOT_FOUND,
        )

    lat, lon = _position(requete)
    distances = {}
    if lat is not None and produit.vendeur.adresse:
        d = distance_km(lat, lon, produit.vendeur.adresse.latitude, produit.vendeur.adresse.longitude)
        if d is not None:
            distances[produit.id] = d

    return Response({"data": ProduitDetailSerializer(
        produit, context={"request": requete, "distances": distances}
    ).data})


@api_view(["GET"])
@permission_classes([AllowAny])
def liste_categories(requete):
    categories = Categorie.objects.annotate(
        nombre_produits=Count(
            "produits",
            filter=Q(produits__est_visible=True,
                     produits__vendeur__statut_validation=StatutValidation.VALIDE),
        )
    ).order_by("nom")
    return Response({"data": CategorieSerializer(categories, many=True).data})


@api_view(["GET"])
@permission_classes([AllowAny])
def liste_boutiques(requete):
    boutiques = (
        Vendeur.objects.select_related("adresse")
        .filter(statut_validation=StatutValidation.VALIDE)
        .annotate(nombre_produits=Count("produits", filter=Q(produits__est_visible=True)))
    )
    if service := requete.query_params.get("type_service"):
        boutiques = boutiques.filter(type_activite=service)

    lat, lon = _position(requete)
    gardes, distances = [], {}
    for boutique in boutiques:
        if boutique.type_activite == TypeService.EXPRESS:
            if lat is None or boutique.adresse is None:
                continue
            d = distance_km(lat, lon, boutique.adresse.latitude, boutique.adresse.longitude)
            if d is None or d > float(boutique.rayon_livraison_km):
                continue
            distances[boutique.id] = d
        gardes.append(boutique)

    return Response({"data": BoutiqueSerializer(
        gardes, many=True, context={"request": requete, "distances": distances}
    ).data})


@api_view(["GET", "POST"])
@permission_classes([EstVendeur])
def mes_produits(requete):
    """Le catalogue du vendeur : le sien, y compris ce qui est masque."""
    profil = getattr(requete.user, "profil_vendeur", None)
    if profil is None:
        return Response(
            {"erreur": {"code": "profil_absent", "message": "Aucune boutique rattachee.",
                        "details": {}}},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if requete.method == "POST":
        if profil.statut_validation != StatutValidation.VALIDE:
            return Response(
                {"erreur": {"code": "non_autorise",
                            "message": "Votre boutique doit etre validee avant de publier.",
                            "details": {}}},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = ProduitEcritureSerializer(data=requete.data)
        serializer.is_valid(raise_exception=True)
        produit = serializer.save(vendeur=profil)
        return Response(
            {"data": ProduitDetailSerializer(produit, context={"request": requete}).data},
            status=status.HTTP_201_CREATED,
        )

    produits = Produit.objects.filter(vendeur=profil).select_related("vendeur", "categorie")
    return Response({"data": ProduitListeSerializer(
        produits, many=True, context={"request": requete}
    ).data})


@api_view(["PATCH", "DELETE"])
@permission_classes([EstVendeur])
def modifier_produit(requete, identifiant):
    profil = getattr(requete.user, "profil_vendeur", None)
    try:
        produit = Produit.objects.get(pk=identifiant, vendeur=profil)
    except Produit.DoesNotExist:
        # 404 et non 403 : repondre « interdit » revelerait qu'un produit
        # existe chez un autre vendeur.
        return Response(status=status.HTTP_404_NOT_FOUND)

    if requete.method == "DELETE":
        # Suppression logique (D-13) : le produit disparait du catalogue mais
        # les commandes passees continuent de le referencer.
        produit.est_visible = False
        produit.save(update_fields=["est_visible"])
        return Response(status=status.HTTP_204_NO_CONTENT)

    serializer = ProduitEcritureSerializer(produit, data=requete.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response({"data": ProduitDetailSerializer(
        produit, context={"request": requete}
    ).data})


# ═══════════════════════════════════════════════════════════════════════════
#  Photos — contrat-medias.md
# ═══════════════════════════════════════════════════════════════════════════

def _produit_du_vendeur(requete, identifiant):
    """Le produit, s'il appartient bien a la boutique de qui appelle.

    404 et non 403 : repondre « interdit » revelerait qu'un produit portant cet
    identifiant existe chez un concurrent.
    """
    profil = getattr(requete.user, "profil_vendeur", None)
    if profil is None:
        return None
    return Produit.objects.filter(pk=identifiant, vendeur=profil).first()


@api_view(["POST"])
@permission_classes([EstVendeur])
@parser_classes([MultiPartParser, FormParser])
def televerser_photos(requete, identifiant):
    produit = _produit_du_vendeur(requete, identifiant)
    if produit is None:
        return Response(status=status.HTTP_404_NOT_FOUND)

    fichiers = requete.FILES.getlist("photos") or requete.FILES.getlist("photo")
    if not fichiers:
        return Response(
            {"erreur": {"code": "validation", "message": "Aucun fichier recu.", "details": {}}},
            status=status.HTTP_400_BAD_REQUEST,
        )

    ajoutees = []
    for fichier in fichiers:
        try:
            url = enregistrer_photo(fichier)
            ajoutees.append(ajouter_photo(produit, url))
        except (FichierRefuse, RegleMetier) as refus:
            # On s'arrete au premier refus, mais on garde ce qui est deja passe :
            # perdre trois photos valides a cause de la quatrieme serait pire.
            return Response(
                {"erreur": {"code": "validation", "message": str(refus),
                            "details": {"acceptees": len(ajoutees)}}},
                status=status.HTTP_400_BAD_REQUEST,
            )

    return Response(
        {"data": PhotoProduitSerializer(
            produit.photos.order_by("ordre"), many=True, context={"request": requete}
        ).data},
        status=status.HTTP_201_CREATED,
    )


@api_view(["PATCH"])
@permission_classes([EstVendeur])
def ordonner_photos(requete, identifiant):
    produit = _produit_du_vendeur(requete, identifiant)
    if produit is None:
        return Response(status=status.HTTP_404_NOT_FOUND)

    try:
        reordonner_photos(produit, [int(x) for x in requete.data.get("ordre", [])])
    except (RegleMetier, ValueError, TypeError) as refus:
        return Response(
            {"erreur": {"code": "validation", "message": str(refus), "details": {}}},
            status=status.HTTP_400_BAD_REQUEST,
        )

    return Response({"data": PhotoProduitSerializer(
        produit.photos.order_by("ordre"), many=True, context={"request": requete}
    ).data})


@api_view(["DELETE"])
@permission_classes([EstVendeur])
def retirer_photo(requete, identifiant, id_photo):
    produit = _produit_du_vendeur(requete, identifiant)
    if produit is None:
        return Response(status=status.HTTP_404_NOT_FOUND)

    photo = PhotoProduit.objects.filter(pk=id_photo, produit=produit).first()
    if photo is None:
        return Response(status=status.HTTP_404_NOT_FOUND)

    chemin = photo.url
    supprimer_photo_du_produit(produit, photo)
    supprimer_photo(chemin)
    return Response({"data": PhotoProduitSerializer(
        produit.photos.order_by("ordre"), many=True, context={"request": requete}
    ).data})


# ═══════════════════════════════════════════════════════════════════════════
#  Stock — scenario 4.4
# ═══════════════════════════════════════════════════════════════════════════

@api_view(["PATCH"])
@permission_classes([EstVendeurOuSonPersonnel])
def modifier_stock(requete, identifiant):
    """Le vendeur ET son personnel ajustent le stock.

    Le gestionnaire prepare les commandes et constate les ecarts : lui refuser
    l'ajustement obligerait a deranger le vendeur pour chaque casse. Il n'a en
    revanche aucun acces aux prix ni au chiffre d'affaires (D-04).
    """
    produit = _produit_accessible(requete, identifiant)
    if produit is None:
        return Response(status=status.HTTP_404_NOT_FOUND)

    try:
        mouvement = ajuster_stock(
            produit,
            quantite=int(requete.data.get("quantite", 0)),
            type_mouvement=requete.data.get("type", TypeMouvement.AJUSTEMENT),
            motif=str(requete.data.get("motif", "")),
            auteur=requete.user,
        )
    except (RegleMetier, ValueError, TypeError) as refus:
        return Response(
            {"erreur": {"code": "validation", "message": str(refus), "details": {}}},
            status=status.HTTP_400_BAD_REQUEST,
        )

    return Response({"data": {
        "stock_disponible": produit.stock_disponible,
        "stock_commandable": produit.stock_commandable,
        "mouvement": MouvementStockSerializer(mouvement).data,
    }})


@api_view(["GET"])
@permission_classes([EstVendeurOuSonPersonnel])
def mouvements_du_produit(requete, identifiant):
    produit = _produit_accessible(requete, identifiant)
    if produit is None:
        return Response(status=status.HTTP_404_NOT_FOUND)

    mouvements = produit.mouvements.select_related("auteur")[:100]
    return Response({"data": MouvementStockSerializer(mouvements, many=True).data})


def _produit_accessible(requete, identifiant):
    """Le produit, pour le vendeur proprietaire ou pour son personnel."""
    utilisateur = requete.user
    profil_vendeur = getattr(utilisateur, "profil_vendeur", None)
    if profil_vendeur is not None:
        return Produit.objects.filter(pk=identifiant, vendeur=profil_vendeur).first()

    profil_gestionnaire = getattr(utilisateur, "profil_gestionnaire", None)
    if profil_gestionnaire is not None and profil_gestionnaire.vendeur_id:
        return Produit.objects.filter(
            pk=identifiant, vendeur_id=profil_gestionnaire.vendeur_id
        ).first()
    return None


@api_view(["GET"])
@permission_classes([EstVendeurOuSonPersonnel])
def stock_bas(requete):
    """Les produits sous leur seuil d'alerte : la premiere chose que le vendeur
    doit voir en arrivant (contrat-web.md)."""
    utilisateur = requete.user
    profil = getattr(utilisateur, "profil_vendeur", None)
    identifiant_vendeur = profil.id if profil else getattr(
        getattr(utilisateur, "profil_gestionnaire", None), "vendeur_id", None
    )
    if identifiant_vendeur is None:
        return Response({"data": []})

    produits = Produit.objects.filter(
        vendeur_id=identifiant_vendeur,
        stock_disponible__lte=models_F_seuil(),
    ).select_related("vendeur")
    return Response({"data": ProduitListeSerializer(
        produits, many=True, context={"request": requete}
    ).data})


def models_F_seuil():
    from django.db.models import F

    return F("seuil_alerte")
