"""Remplit le catalogue de demonstration, images comprises (decision D-24).

    python manage.py seed_catalogue

Trois niveaux, du meilleur au dernier recours :

1. **Tes propres fichiers**, s'ils existent : `donnees-demo/images/<slug>.jpg`.
   Ils ont toujours la priorite.
2. **Le telechargement** depuis une liste figee de photos sous licence libre
   (Unsplash, ou Flickr par mots-cles quand aucune photo Unsplash ne convenait).
   Chaque image a ete regardee avant d'entrer dans la liste.
3. **Une image fabriquee** par Pillow — un degrade aux couleurs de la marque
   portant le nom du produit. Hors ligne, ou si une adresse est morte, la
   demonstration ne casse jamais parce qu'un site tiers a bouge.

Les images passent par le **meme traitement** qu'un televersement de vendeur :
recadrage, conversion en WebP, retrait des metadonnees. Le peuplement teste
donc la chaine d'images au lieu de la contourner.
"""
import hashlib
import io
import os
from urllib.request import Request, urlopen

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify
from PIL import Image, ImageDraw, ImageFont

from catalogue.models import Categorie, PhotoProduit, Produit
from comptes.models import Vendeur

# Le regroupement des categories en univers.
UNIVERS = {
    "Plats": "Restauration",
    "Entrees": "Restauration",
    "Desserts": "Restauration",
    "Audio": "High-tech",
    "Informatique": "High-tech",
    "Telephonie": "High-tech",
    "Accessoires": "High-tech",
}

LARGEUR = 900
HAUTEUR = 675
DOSSIER = "produits"

# Photos sous licence libre. La liste est figee et versionnee : le script ne
# parcourt jamais le web au hasard pour ramasser des images dont personne ne
# connait la licence.
#
# Chaque image a ete REGARDEE avant d'entrer dans cette liste. C'est la seule
# verification possible : rien, dans une URL, ne dit qu'une photo correspond
# au produit. Une premiere version montrait une chaise pour un clavier
# mecanique et un appareil photo pour un sac a dos.
#
# Deux sources, selon ce qui donnait le meilleur resultat :
#   ("unsplash", "<identifiant>")        photo choisie, qualite studio
#   ("flickr", "<mots-cles>", <verrou>)  recherche par mots-cles, verrou fige
#                                        la photo pour qu'elle ne change plus
CATALOGUE = [
    # ── Chez Karim — Express, restauration ──────────────────────────────
    ("Chez Karim", "Plats", "Bol de ramen maison",
     "Nouilles fraiches, bouillon mijote douze heures, oeuf mollet.",
     1290, 40, ("flickr", "ramen,noodles", 3)),
    ("Chez Karim", "Plats", "Burger du marche",
     "Boeuf charolais, cheddar affine, pain brioche du jour.",
     1450, 35, ("unsplash", "1550547660-d9450f859349")),
    ("Chez Karim", "Plats", "Pizza napolitaine",
     "Pate levee 48 heures, tomates San Marzano, mozzarella di bufala.",
     1350, 28, ("unsplash", "1565299624946-b28f40a0ae38")),
    ("Chez Karim", "Plats", "Assiette du chef",
     "Le plat du jour, compose le matin selon le marche.",
     1690, 12, ("unsplash", "1504674900247-0877df9cc836")),
    ("Chez Karim", "Entrees", "Salade de saison",
     "Legumes croquants, graines torrefiees, vinaigrette maison.",
     890, 50, ("unsplash", "1540189549336-e6e99c3679fe")),
    ("Chez Karim", "Desserts", "Tarte du jour",
     "Patisserie preparee le matin, en quantite limitee.",
     620, 0, ("flickr", "tart,pastry", 3)),

    # ── TechSophie — Standard, electronique reconditionnee ──────────────
    ("TechSophie", "Audio", "Casque a reduction de bruit",
     "Reconditionne grade A, batterie changee, garantie deux ans.",
     18900, 14, ("unsplash", "1505740420928-5e560c06d30e")),
    ("TechSophie", "Audio", "Enceinte portable",
     "Autonomie douze heures, resistante aux projections.",
     7900, 22, ("flickr", "bluetooth,speaker", 1)),
    ("TechSophie", "Informatique", "Ordinateur portable 14 pouces",
     "Reconditionne, 16 Go de memoire, disque 512 Go.",
     64900, 6, ("unsplash", "1496181133206-80ce9b88a853")),
    ("TechSophie", "Telephonie", "Telephone reconditionne",
     "Grade A, batterie neuve, debloque tout operateur.",
     32900, 9, ("unsplash", "1511707171634-5f897ff02aa9")),
    ("TechSophie", "Accessoires", "Montre connectee",
     "Suivi d'activite, autonomie sept jours.",
     12900, 18, ("unsplash", "1523275335684-37898b6baf30")),
    ("TechSophie", "Accessoires", "Lunettes de soleil polarisees",
     "Verres categorie 3, monture recyclee.",
     4900, 31, ("unsplash", "1572635196237-14b3f281503f")),
    ("TechSophie", "Accessoires", "Sac a dos urbain",
     "Compartiment ordinateur 15 pouces, tissu recycle.",
     6900, 25, ("flickr", "backpack,leather", 3)),
    ("TechSophie", "Informatique", "Clavier mecanique",
     "Switches silencieux, retroeclairage, sans fil.",
     8900, 0, ("flickr", "keyboard,gaming", 2)),
]


class Command(BaseCommand):
    help = "Cree les categories, les produits et leurs images de demonstration."

    def add_arguments(self, analyseur):
        analyseur.add_argument(
            "--hors-ligne",
            action="store_true",
            dest="hors_ligne",
            help="N'essaie meme pas de telecharger : fabrique toutes les images.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        self.hors_ligne = options["hors_ligne"]
        self.telecharges = 0
        self.fabriquees = 0
        self.fournies = 0

        boutiques = {v.nom_boutique: v for v in Vendeur.objects.all()}
        if not boutiques:
            self.stdout.write(self.style.WARNING(
                "Aucune boutique : lance d'abord `python manage.py seed_demo`."
            ))
            return

        categories = {}
        crees = 0

        for nom_boutique, nom_categorie, nom, description, prix, stock, photo in CATALOGUE:
            vendeur = boutiques.get(nom_boutique)
            if vendeur is None:
                continue

            if nom_categorie not in categories:
                categorie, _ = Categorie.objects.get_or_create(
                    slug=slugify(nom_categorie), defaults={"nom": nom_categorie}
                )
                # Sept categories a plat ne disent rien. Regroupees en deux
                # univers, elles se lisent d'un coup d'oeil — et le modele
                # prevoyait deja la reflexivite pour cela (A13 du MCD).
                parente = self.univers(UNIVERS.get(nom_categorie, "Autres"))
                if categorie.parente_id != parente.id:
                    categorie.parente = parente
                    categorie.save(update_fields=["parente"])
                categories[nom_categorie] = categorie

            if Produit.objects.filter(vendeur=vendeur, nom=nom).exists():
                continue

            produit = Produit.objects.create(
                vendeur=vendeur,
                categorie=categories[nom_categorie],
                nom=nom,
                description=description,
                prix_unitaire_centimes=prix,
                stock_disponible=stock,
                seuil_alerte=5,
                poids_grammes=400 if vendeur.type_activite == "EXPRESS" else 1200,
            )

            chemin = self.obtenir_image(nom, photo)
            produit.image_principale_url = chemin
            produit.save(update_fields=["image_principale_url"])
            PhotoProduit.objects.create(
                produit=produit, url=chemin, ordre=1,
                texte_alternatif=f"{nom} — {vendeur.nom_boutique}",
            )
            crees += 1

        self.stdout.write("")
        if crees:
            self.stdout.write(self.style.SUCCESS(f"Catalogue : {crees} produit(s) cree(s)."))
            self.stdout.write(
                f"  images : {self.fournies} fournie(s), {self.telecharges} telechargee(s), "
                f"{self.fabriquees} fabriquee(s)"
            )
        else:
            self.stdout.write(self.style.SUCCESS("Catalogue deja en place."))
        self.stdout.write("")

    def univers(self, nom):
        """La categorie parente, creee au besoin."""
        if not hasattr(self, "_univers"):
            self._univers = {}
        if nom not in self._univers:
            self._univers[nom], _ = Categorie.objects.get_or_create(
                slug=slugify(nom), defaults={"nom": nom}
            )
        return self._univers[nom]

    # ── Les images ───────────────────────────────────────────────────────

    def obtenir_image(self, nom_produit, source):
        """Renvoie le chemin public de l'image, quelle que soit sa provenance."""
        slug = slugify(nom_produit)
        dossier = os.path.join(settings.MEDIA_ROOT, DOSSIER)
        os.makedirs(dossier, exist_ok=True)
        destination = os.path.join(dossier, f"{slug}.webp")
        chemin_public = f"{settings.MEDIA_URL}{DOSSIER}/{slug}.webp"

        if os.path.exists(destination):
            return chemin_public

        image = self.image_fournie(slug) or self.image_telechargee(source)
        if image is None:
            image = self.image_fabriquee(nom_produit)
            self.fabriquees += 1

        self.traiter(image).save(destination, "WEBP", quality=82, method=5)
        return chemin_public

    def image_fournie(self, slug):
        """Tes propres fichiers, s'ils existent. Ils priment sur tout le reste."""
        dossier = os.path.join(settings.RACINE.parent, "donnees-demo", "images")
        for extension in ("jpg", "jpeg", "png", "webp"):
            chemin = os.path.join(dossier, f"{slug}.{extension}")
            if os.path.exists(chemin):
                self.fournies += 1
                return Image.open(chemin)
        return None

    def image_telechargee(self, source):
        if self.hors_ligne:
            return None

        if source[0] == "unsplash":
            url = f"https://images.unsplash.com/photo-{source[1]}?w={LARGEUR}&q=80"
        else:
            # Le verrou fige la photo : sans lui, la meme adresse renvoie une
            # image differente a chaque appel, et le catalogue change de tete
            # a chaque peuplement.
            url = f"https://loremflickr.com/{LARGEUR}/{HAUTEUR}/{source[1]}?lock={source[2]}"
        try:
            donnees = urlopen(
                Request(url, headers={"User-Agent": "RivDinde/0.1 (projet etudiant)"}),
                timeout=12,
            ).read()
            image = Image.open(io.BytesIO(donnees))
            image.load()
            self.telecharges += 1
            return image
        except Exception:
            # Site injoignable, adresse morte, pas de reseau : on fabrique.
            return None

    def image_fabriquee(self, nom_produit):
        """Le dernier recours : un degrade aux couleurs de la marque.

        Deterministe — le meme produit donne toujours la meme image, ce qui
        evite qu'un catalogue change d'apparence a chaque peuplement.
        """
        graine = int(hashlib.md5(nom_produit.encode()).hexdigest()[:6], 16)
        base = (90 + graine % 60, 50 + graine // 60 % 40, 30 + graine // 2400 % 30)

        image = Image.new("RGB", (LARGEUR, HAUTEUR), base)
        dessin = ImageDraw.Draw(image)
        for y in range(HAUTEUR):
            facteur = 1 - y / (HAUTEUR * 1.6)
            dessin.line([(0, y), (LARGEUR, y)], fill=tuple(int(c * facteur) for c in base))

        try:
            police = ImageFont.truetype("arial.ttf", 44)
        except OSError:
            police = ImageFont.load_default()
        dessin.text((48, HAUTEUR - 120), nom_produit, font=police, fill=(240, 163, 68))
        return image

    def traiter(self, image):
        """Le meme traitement qu'un televersement de vendeur (contrat-medias).

        Conversion, recadrage au format de la grille, retrait des metadonnees :
        une photo prise au telephone porte les coordonnees GPS de qui l'a prise.
        """
        image = image.convert("RGB")

        # Recadrage centre au format 4:3, pour que la grille du catalogue ne
        # soit pas un patchwork de hauteurs differentes.
        ratio_cible = LARGEUR / HAUTEUR
        largeur, hauteur = image.size
        if largeur / hauteur > ratio_cible:
            nouvelle_largeur = int(hauteur * ratio_cible)
            gauche = (largeur - nouvelle_largeur) // 2
            image = image.crop((gauche, 0, gauche + nouvelle_largeur, hauteur))
        else:
            nouvelle_hauteur = int(largeur / ratio_cible)
            haut = (hauteur - nouvelle_hauteur) // 2
            image = image.crop((0, haut, largeur, haut + nouvelle_hauteur))

        image = image.resize((LARGEUR, HAUTEUR), Image.LANCZOS)

        # Une image reconstruite depuis ses seuls pixels ne porte plus aucune
        # metadonnee — ni EXIF, ni GPS.
        propre = Image.new("RGB", image.size)
        propre.putdata(list(image.getdata()))
        return propre
