import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'

import { useAuthentification, type Role } from './stores/authentification'

// Trois niveaux d'acces, et un seul mot pour chacun :
//
//   public  le catalogue, la fiche produit, la page « rejoindre ». Un visiteur
//           regarde AVANT de creer un compte (D-03) — c'est la raison d'etre
//           de cette distinction.
//   auth    connexion et inscription : reserves a qui n'est pas encore entre.
//   prive   les espaces de travail.
export type Acces = 'public' | 'auth' | 'prive'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'vitrine',
    component: () => import('./vues/publiques/Vitrine.vue'),
    meta: { acces: 'public' },
  },
  {
    path: '/produit/:id',
    name: 'produit',
    component: () => import('./vues/publiques/FicheProduit.vue'),
    meta: { acces: 'public' },
  },
  {
    path: '/boutiques',
    name: 'boutiques',
    component: () => import('./vues/publiques/Boutiques.vue'),
    meta: { acces: 'public' },
  },
  {
    path: '/commande',
    name: 'commande',
    component: () => import('./vues/client/PasserCommande.vue'),
    // Publique : on prepare sa commande sans compte, on le cree pour valider.
    meta: { acces: 'public' },
  },
  {
    path: '/rejoindre',
    name: 'rejoindre',
    component: () => import('./vues/publiques/Rejoindre.vue'),
    meta: { acces: 'public' },
  },
  {
    path: '/connexion',
    name: 'connexion',
    component: () => import('./vues/Connexion.vue'),
    meta: { acces: 'auth', plein: true },
  },
  {
    path: '/inscription',
    name: 'inscription',
    component: () => import('./vues/Inscription.vue'),
    meta: { acces: 'auth', plein: true },
  },
  {
    path: '/en-attente',
    name: 'en-attente',
    component: () => import('./vues/EnAttente.vue'),
    meta: { acces: 'prive', plein: true },
  },
  {
    path: '/espace',
    name: 'espace',
    component: () => import('./vues/Accueil.vue'),
    meta: { acces: 'prive' },
  },
  {
    path: '/espace/catalogue',
    name: 'vendeur-catalogue',
    component: () => import('./vues/vendeur/CatalogueVendeur.vue'),
    meta: { acces: 'prive' },
  },
  {
    path: '/espace/catalogue/nouveau',
    name: 'vendeur-nouveau',
    component: () => import('./vues/vendeur/FicheProduitVendeur.vue'),
    meta: { acces: 'prive' },
  },
  {
    path: '/espace/catalogue/:id',
    name: 'vendeur-produit',
    component: () => import('./vues/vendeur/FicheProduitVendeur.vue'),
    meta: { acces: 'prive' },
  },
  {
    path: '/mes-commandes',
    name: 'mes-commandes',
    component: () => import('./vues/client/MesCommandes.vue'),
    meta: { acces: 'prive' },
  },
  {
    path: '/espace/commandes',
    name: 'vendeur-commandes',
    component: () => import('./vues/vendeur/CommandesRecues.vue'),
    meta: { acces: 'prive' },
  },
  {
    path: '/espace/validations',
    name: 'admin-validations',
    component: () => import('./vues/admin/Validations.vue'),
    meta: { acces: 'prive' },
  },
  { path: '/:reste(.*)*', redirect: '/' },
]

export const routeur = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior: (vers, depuis, position) => position ?? { top: 0 },
})

export type EtatSession = {
  estConnecte: boolean
  enAttenteDeValidation: boolean
  role: Role | null
}
export type Destination = { nom: string | null | undefined; acces: Acces }

/** Ou atterrit un compte apres connexion.
 *
 *  Un client reste sur la vitrine : c'est la qu'il commande. Les autres roles
 *  vont dans leur espace de travail, qui n'a rien a voir avec le magasin.
 */
export function accueilDuRole(role: Role | null): string {
  return role === 'CLIENT' || role === null ? 'vitrine' : 'espace'
}

/**
 * La decision de navigation, sortie du routeur pour etre testable.
 *
 * Renvoie `true` pour laisser passer, ou le nom de la route vers laquelle
 * rediriger. C'est un CONFORT, pas une securite : le veritable controle est
 * cote serveur (scenario 14.1), ou un role qui appelle l'URL d'un autre
 * recoit 403.
 */
export function deciderNavigation(session: EtatSession, vers: Destination): true | string {
  // Le catalogue est ouvert a tout le monde, connecte ou non.
  if (vers.acces === 'public') {
    return true
  }

  if (vers.acces === 'auth') {
    return session.estConnecte ? accueilDuRole(session.role) : true
  }

  if (!session.estConnecte) {
    return 'connexion'
  }

  // Un vendeur ou un livreur en attente de validation n'a acces qu'a son
  // ecran d'attente — et inversement, un compte actif n'a rien a y faire.
  if (session.enAttenteDeValidation) {
    return vers.nom === 'en-attente' ? true : 'en-attente'
  }
  return vers.nom === 'en-attente' ? accueilDuRole(session.role) : true
}

routeur.beforeEach((vers) => {
  const session = useAuthentification()
  const decision = deciderNavigation(
    {
      estConnecte: session.estConnecte,
      enAttenteDeValidation: session.enAttenteDeValidation,
      role: session.role,
    },
    { nom: vers.name as string | undefined, acces: (vers.meta.acces as Acces) ?? 'prive' },
  )
  return decision === true ? true : { name: decision }
})
