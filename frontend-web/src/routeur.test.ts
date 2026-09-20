import { describe, expect, it } from 'vitest'

import { accueilDuRole, deciderNavigation, type Acces } from './routeur'

const VISITEUR = { estConnecte: false, enAttenteDeValidation: false, role: null }
const CLIENT = { estConnecte: true, enAttenteDeValidation: false, role: 'CLIENT' as const }
const VENDEUR = { estConnecte: true, enAttenteDeValidation: false, role: 'VENDEUR' as const }
const EN_ATTENTE = { estConnecte: true, enAttenteDeValidation: true, role: 'VENDEUR' as const }

const vers = (nom: string, acces: Acces) => ({ nom, acces })

describe('acces au catalogue public', () => {
  // Le coeur de la decision D-03 : on regarde avant de creer un compte.
  it('laisse un visiteur entrer sur la vitrine', () => {
    expect(deciderNavigation(VISITEUR, vers('vitrine', 'public'))).toBe(true)
  })

  it('laisse un visiteur ouvrir une fiche produit', () => {
    expect(deciderNavigation(VISITEUR, vers('produit', 'public'))).toBe(true)
  })

  it('laisse un visiteur lire la page « rejoindre »', () => {
    expect(deciderNavigation(VISITEUR, vers('rejoindre', 'public'))).toBe(true)
  })

  it('laisse aussi un compte connecte revenir sur la vitrine', () => {
    expect(deciderNavigation(CLIENT, vers('vitrine', 'public'))).toBe(true)
    expect(deciderNavigation(VENDEUR, vers('vitrine', 'public'))).toBe(true)
  })
})

describe('ecrans de connexion et d inscription', () => {
  it('les laisse ouverts a un visiteur', () => {
    expect(deciderNavigation(VISITEUR, vers('connexion', 'auth'))).toBe(true)
    expect(deciderNavigation(VISITEUR, vers('inscription', 'auth'))).toBe(true)
  })

  it('renvoie un client deja connecte vers la vitrine', () => {
    expect(deciderNavigation(CLIENT, vers('connexion', 'auth'))).toBe('vitrine')
  })

  it('renvoie un vendeur deja connecte vers son espace', () => {
    expect(deciderNavigation(VENDEUR, vers('connexion', 'auth'))).toBe('espace')
  })
})

describe('espaces prives', () => {
  it('renvoie un visiteur vers la connexion', () => {
    expect(deciderNavigation(VISITEUR, vers('espace', 'prive'))).toBe('connexion')
  })

  it('laisse un compte actif entrer dans son espace', () => {
    expect(deciderNavigation(VENDEUR, vers('espace', 'prive'))).toBe(true)
  })
})

describe('compte en attente de validation', () => {
  it('atteint son ecran d attente', () => {
    expect(deciderNavigation(EN_ATTENTE, vers('en-attente', 'prive'))).toBe(true)
  })

  it('est ramene vers cet ecran depuis un espace de travail', () => {
    expect(deciderNavigation(EN_ATTENTE, vers('espace', 'prive'))).toBe('en-attente')
  })

  it('peut quand meme parcourir le catalogue public', () => {
    expect(deciderNavigation(EN_ATTENTE, vers('vitrine', 'public'))).toBe(true)
  })

  it('ne boucle pas : la redirection mene a une destination acceptee', () => {
    const premiere = deciderNavigation(EN_ATTENTE, vers('espace', 'prive'))
    expect(premiere).toBe('en-attente')
    expect(deciderNavigation(EN_ATTENTE, vers(premiere as string, 'prive'))).toBe(true)
  })

  it('interdit l ecran d attente a un compte actif', () => {
    expect(deciderNavigation(VENDEUR, vers('en-attente', 'prive'))).toBe('espace')
    expect(deciderNavigation(CLIENT, vers('en-attente', 'prive'))).toBe('vitrine')
  })
})

describe('atterrissage apres connexion', () => {
  it('envoie le client sur la vitrine, ou il commande', () => {
    expect(accueilDuRole('CLIENT')).toBe('vitrine')
  })

  it('envoie les autres roles dans leur espace de travail', () => {
    for (const role of ['VENDEUR', 'GESTIONNAIRE', 'LIVREUR', 'ADMIN'] as const) {
      expect(accueilDuRole(role)).toBe('espace')
    }
  })
})
