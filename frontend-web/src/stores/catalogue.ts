// Le catalogue, partage par la sidebar (les filtres) et par la page (la grille).
//
// Un seul magasin pour les deux, sinon il faudrait faire descendre une dizaine
// de proprietes a travers la coquille — et le catalogue public finirait par
// diverger de celui de l'espace, ce qu'on veut precisement eviter.
import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import { appelerComplet } from '../api/client'
import type { Produit } from '../composants/CarteProduit.vue'
import { usePosition } from './position'

export type Categorie = { slug: string; nom: string; univers: string; nombre: number }
export type Univers = { nom: string; nombre: number; categories: Categorie[] }
export type BoutiqueFacette = { id: number; nom: string; type_service: string; nombre: number }

type Reponse = {
  data: Produit[]
  meta: {
    total: number
    total_avant_filtres: number
    facettes: { univers: Univers[]; boutiques: BoutiqueFacette[] }
  }
}

export const useCatalogue = defineStore('catalogue', () => {
  const produits = ref<Produit[]>([])
  const univers = ref<Univers[]>([])
  const boutiques = ref<BoutiqueFacette[]>([])
  const chargement = ref(true)

  const categorie = ref<string | undefined>()
  const boutique = ref<string | undefined>()
  const service = ref<string | undefined>()
  const recherche = ref('')

  const filtreActif = computed(
    () => Boolean(categorie.value || boutique.value || service.value || recherche.value.trim()),
  )

  function parametres() {
    const position = usePosition()
    const morceaux = [position.parametres]
    if (categorie.value) morceaux.push(`categorie=${encodeURIComponent(categorie.value)}`)
    if (boutique.value) morceaux.push(`boutique=${encodeURIComponent(boutique.value)}`)
    if (service.value) morceaux.push(`type_service=${service.value}`)
    if (recherche.value.trim())
      morceaux.push(`recherche=${encodeURIComponent(recherche.value.trim())}`)
    const requete = morceaux.filter(Boolean).join('&')
    return requete ? `?${requete}` : ''
  }

  let dernierAppel = 0

  async function charger() {
    chargement.value = true
    const appel = ++dernierAppel
    try {
      const reponse = await appelerComplet<Reponse>(`/produits${parametres()}`)
      // Une reponse arrivee en retard ne doit pas ecraser une plus recente :
      // en tapant vite, les requetes ne reviennent pas dans l'ordre.
      if (appel !== dernierAppel) return
      produits.value = reponse.data
      univers.value = reponse.meta.facettes.univers
      boutiques.value = reponse.meta.facettes.boutiques
    } catch {
      if (appel !== dernierAppel) return
      produits.value = []
      univers.value = []
      boutiques.value = []
    } finally {
      if (appel === dernierAppel) chargement.value = false
    }
  }

  let minuteur: ReturnType<typeof setTimeout> | undefined

  /** Recherche instantanee : on attend 250 ms apres la derniere frappe. */
  function chercher(valeur: string) {
    recherche.value = valeur
    clearTimeout(minuteur)
    minuteur = setTimeout(charger, 250)
  }

  function basculer(champ: 'categorie' | 'boutique' | 'service', valeur: string | undefined) {
    const cible = { categorie, boutique, service }[champ]
    cible.value = cible.value === valeur ? undefined : valeur
    charger()
  }

  function toutEffacer() {
    categorie.value = undefined
    boutique.value = undefined
    service.value = undefined
    recherche.value = ''
    charger()
  }

  return {
    produits, univers, boutiques, chargement,
    categorie, boutique, service, recherche, filtreActif,
    charger, chercher, basculer, toutEffacer,
  }
})
