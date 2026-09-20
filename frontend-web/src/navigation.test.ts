import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'

import App from './App.vue'
import { routeur } from './routeur'

describe('navigation reelle avec le vrai routeur', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.stubGlobal('localStorage', { getItem: () => null, setItem: () => {}, removeItem: () => {} })
    // Une charge utile plausible : un test qui nourrit du vide ne prouve
    // rien sur le comportement reel des ecrans.
    vi.stubGlobal(
      'fetch',
      vi.fn(async (url: string) => ({
        ok: true,
        status: 200,
        json: async () =>
          String(url).includes('/produits/')
            ? {
                data: {
                  id: 7, nom: 'Casque', description: 'Un casque.', prix_centimes: 18900,
                  image: '', photos: [], disponible: true, stock_disponible: 5,
                  distance_km: null, categorie: null,
                  boutique: { id: 1, nom: 'TechSophie', type_service: 'STANDARD', ville: 'Lyon' },
                },
              }
            : { data: [], meta: { total: 0, total_avant_filtres: 0,
                                  facettes: { univers: [], boutiques: [] } } },
      })),
    )
  })

  it('un visiteur passe de la vitrine a rejoindre, connexion, inscription, fiche produit', async () => {
    await routeur.push('/')
    await routeur.isReady()
    mount(App, { global: { plugins: [routeur] } })

    for (const chemin of ['/rejoindre', '/connexion', '/inscription', '/produit/7', '/']) {
      await routeur.push(chemin)
      await routeur.isReady()
      expect(routeur.currentRoute.value.path).toBe(chemin)
    }
  })

  it('un espace prive renvoie bien un visiteur vers la connexion', async () => {
    await routeur.push('/espace')
    await routeur.isReady()
    expect(routeur.currentRoute.value.name).toBe('connexion')
  })
})
