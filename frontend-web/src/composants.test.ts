import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import CarteProduit from './composants/CarteProduit.vue'
import CoquilleApp from './composants/CoquilleApp.vue'
import { routeur } from './routeur'

// On monte avec le VRAI routeur : un routeur de test allege laisserait passer
// un lien qui pointe vers une route inexistante — exactement le bug qu'on
// cherche a attraper.
describe('la navigation existe vraiment', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.stubGlobal('localStorage', {
      getItem: () => null, setItem: () => {}, removeItem: () => {},
    })
    vi.stubGlobal('fetch', vi.fn(async () => ({
      ok: true, status: 200,
      json: async () => ({ data: [], meta: { total: 0, total_avant_filtres: 0,
                                             facettes: { univers: [], boutiques: [] } } }),
    })))
  })

  it('la coquille porte des liens cliquables vers des routes existantes', async () => {
    await routeur.push('/')
    await routeur.isReady()

    const composant = mount(CoquilleApp, { global: { plugins: [routeur] } })
    const liens = composant.findAll('a').map((a) => a.attributes('href'))

    // Un visiteur doit pouvoir regarder le catalogue, decouvrir comment
    // rejoindre la plateforme, et entrer.
    expect(liens).toContain('/')
    expect(liens).toContain('/boutiques')
    expect(liens).toContain('/rejoindre')
    expect(liens).toContain('/connexion')
    expect(liens).toContain('/inscription')
  })

  it('la carte produit entiere mene a la fiche', async () => {
    await routeur.push('/')
    await routeur.isReady()

    const composant = mount(CarteProduit, {
      global: { plugins: [routeur] },
      props: {
        produit: {
          id: 7, nom: 'Casque', prix_centimes: 18900, image: '/media/x.webp',
          disponible: true, distance_km: null,
          boutique: { id: 1, nom: 'TechSophie', type_service: 'STANDARD', ville: 'Lyon' },
        },
      },
    })

    expect(composant.find('a').attributes('href')).toBe('/produit/7')
  })
})
