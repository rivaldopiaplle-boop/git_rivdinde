# Donnees de demonstration

Ce dossier alimente la commande `python manage.py seed_demo`, qui remplit une
base vide avec un catalogue presentable : des boutiques, des produits, des
comptes de demonstration pour les cinq roles.

## Les images (decision D-24)

**Tu n'as rien a faire.** Le script telecharge lui-meme les photos depuis une
liste figee de sources sous licence libre (Unsplash, Pexels), et les fait
passer par le meme circuit de televersement qu'un vrai vendeur — le peuplement
teste donc la chaine d'envoi au lieu de la contourner.

Hors ligne, ou si une adresse est morte, une image de repli est fabriquee : un
aplat de couleur portant le nom du produit. La demonstration ne casse jamais
parce qu'un site tiers a bouge.

## Si tu veux ton propre catalogue

Depose tes fichiers dans `images/`, nommes d'apres l'identifiant du produit :

```
donnees-demo/images/bol-ramen.jpg
donnees-demo/images/casque-audio.jpg
```

Le script les prefere a tout telechargement. C'est une option, pas une corvee.

Le detail complet — formats, tailles, stockage — est dans
[contrat-medias.md](../plan-organisation/03-contrats/contrat-medias.md).
