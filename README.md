<div align="center">

<img src="frontend-web/public/logo-rivdinde-256.webp" width="150" alt="RivDinde">

# RivDinde

**commander, livrer, suivre**

Une plateforme de commerce et de livraison à deux régimes :
**Express** (restauration, trajet direct) et **Standard** (colis, entrepôt, tournées groupées).

</div>

---

> **Ce dépôt est une version antérieure, volontairement allégée, et il n'évolue plus.**
> Il existe pour qu'un recruteur puisse lire du code sans récupérer le projet entier.
> La version en ligne est bien plus avancée : cinq métiers avec leurs écrans, application
> mobile, paiement partagé entre les vendeurs, tournées de livraison, mise en ligne
> automatisée et essais rejoués à chaque modification. Ce dépôt-là est privé. Sur demande,
> l'accès en lecture peut être ouvert le temps d'un entretien.
>
> En ligne : https://git-e-commerce-livraison-v2.vercel.app
> Portfolio : https://git-portfolio-rivaldo.vercel.app/projets/rivdinde

## Démarrer

Une seule commande, depuis la racine :

```powershell
python demarrer.py
```

Elle monte la base, prépare l'environnement, applique les migrations et lance
l'API et le front. À la fin, quatre adresses :

| | |
|---|---|
| Front web | http://localhost:5173 |
| API | http://localhost:8000/api/v1/sante |
| Administration Django | http://localhost:8000/admin/ |
| Courriels capturés | http://localhost:8026 |

Les ports de la base et des courriels (5433, 1026, 8026) sont volontairement
décalés des ports habituels : un autre projet peut occuper 5432 et 8025 sur la
même machine, et les deux doivent pouvoir tourner ensemble.

Autres usages :

```powershell
python demarrer.py --etat        # ce qui tourne, ce qui répond
python demarrer.py --sans-web    # API seule
python demarrer.py --preparer    # installe et migre, sans rien lancer
python demarrer.py --arreter     # arrête les conteneurs
```

**Prérequis** : Python 3.10 ou plus, Node 20 ou plus, Docker Desktop. Le script
vérifie tout et le dit clairement s'il manque quelque chose — et si le terminal
utilise un vieux Python alors qu'un récent est installé, il repart tout seul avec
le bon. Détail dans
[ta-part-du-travail.md](plan-organisation/00-pilotage/ta-part-du-travail.md).

**Aucune clé n'est nécessaire pour démarrer.** Sans Stripe, sans Cloudinary,
sans compte nulle part, le projet tourne : les services externes ont chacun un
simulateur local.

---

## Ce que c'est

Cinq rôles, deux circuits de livraison, un seul paiement même quand la commande
concerne plusieurs boutiques.

| Rôle | Support | Ce qu'il fait |
|---|---|---|
| **Client** | Web + mobile | Parcourt, commande, paie, suit, note |
| **Vendeur** | Web | Catalogue, stock, commandes entrantes, son personnel |
| **Gestionnaire** | Web | Prépare — pour un vendeur, ou dans un entrepôt |
| **Livreur** | Mobile | Une course à la fois (Express) ou une tournée (Standard) |
| **Admin** | Web | Valide les comptes, arbitre, surveille |

Un panier mixte se découpe tout seul : une commande par boutique Express, une
commande Standard multi-vendeur qui transite par l'entrepôt — et un seul
règlement pour le client, réparti par Stripe Connect.

---

## Structure

```
rivdinde/
├── plan-organisation/     Toute la conception : décisions, modèle, contrats, maquettes
├── backend/               Django 5 + Django REST Framework
├── frontend-web/          Vue 3 + Vite + TypeScript
├── frontend-mobile/       Ionic Vue + Capacitor          (tranche 7)
├── donnees-demo/          Catalogue et images de démonstration
├── docker-compose.yml     Postgres + attrapeur de courriels
└── demarrer.py            Une commande pour tout lancer
```

---

## La conception avant le code

Tout ce que le code applique est écrit avant, dans
[`plan-organisation/`](plan-organisation/README.md) : **30 décisions motivées**,
un modèle de **33 entités**, sept contrats, et des maquettes des cinq rôles.

| Pour savoir… | Ouvrir |
|---|---|
| Où en est le projet, quoi faire ensuite | [plan-organisation/README.md](plan-organisation/README.md) |
| Ce que le MVP contient, et ce qu'il refuse | [perimetre-et-mvp.md](plan-organisation/01-produit/perimetre-et-mvp.md) |
| Pourquoi tel choix technique | [journal-decisions.md](plan-organisation/00-pilotage/journal-decisions.md) |
| L'équivalent Django/Vue de NestJS/React | [de-nestjs-react-a-django-vue.md](plan-organisation/05-execution/de-nestjs-react-a-django-vue.md) |
| Le modèle de données | [mcd.html](plan-organisation/02-modele/mcd.html) · [dictionnaire-donnees.md](plan-organisation/02-modele/dictionnaire-donnees.md) |
| L'identité visuelle | [identite-visuelle.html](plan-organisation/04-maquettes/identite-visuelle.html) |

---

## État

**Tranches 0 à 2 sur 11.** Le socle tourne, les comptes fonctionnent, et le
catalogue est en ligne :

- **33 entités** en base, inscription et connexion par rôle, un vendeur bloqué
  tant qu'un administrateur ne l'a pas validé ;
- une **vitrine publique** — on regarde avant de créer un compte — avec bandeau
  « Livrer à … », filtres à facettes, grille de produits et fiche détaillée ;
- le **filtrage Express par rayon** : depuis Lyon, les boutiques proches
  apparaissent avec leur distance ; depuis Marseille, elles disparaissent ;
- **14 produits de démonstration** avec de vraies photos, et huit comptes
  nommés d'après les personae des scénarios.

**93 tests** (73 backend, 20 front), `ruff` sans reproche, TypeScript strict.

Le parcours d'achat est complet : catalogue public, panier sans compte qui suit
à la connexion, aperçu du découpage avant validation, commandes créées selon la
règle Express/Standard, préparation côté vendeur, validations côté admin.

Côté vendeur : catalogue avec boutons-icônes, fiche produit à trois onglets,
téléversement de photos qui vérifie le contenu réel des fichiers et retire les
métadonnées, et un stock qui refuse tout ajustement sans motif.

Le plan des onze tranches, chacune avec son test de sortie, est dans
[demarrage-projet.md](plan-organisation/05-execution/demarrage-projet.md).

---

## Pile technique

Django 5 · Django REST Framework · PostgreSQL · Vue 3 · Vite · TypeScript ·
Pinia · Ionic + Capacitor · Docker · GitHub Actions · Stripe Connect · Neon ·
Render · Vercel · Cloudinary

Et ce qu'on a **refusé** — Celery, Redis, Elasticsearch, PostGIS, GraphQL,
microservices — avec les raisons, dans
[stack-technique.md](plan-organisation/05-execution/stack-technique.md).
