// L'etat de session : qui est connecte, avec quel role, et dans quel statut.
//
// Pinia remplace ici ce que le projet banque faisait avec le Context API et
// TanStack Query reunis. Un seul magasin, parce qu'il n'y a qu'une session.
import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import { api, poserJeton } from '../api/client'
import { poserJetonVendeur } from '../api/vendeur'

export type Role = 'CLIENT' | 'VENDEUR' | 'GESTIONNAIRE' | 'LIVREUR' | 'ADMIN'

export type Utilisateur = {
  id: number
  email: string
  nom: string
  prenom: string
  telephone: string
  role: Role
  statut_compte: 'ACTIF' | 'EN_ATTENTE_VALIDATION' | 'SUSPENDU' | 'DESACTIVE'
}

type Identite = {
  utilisateur: Utilisateur
  profil: Record<string, unknown> | null
  acces: string
  rafraichissement: string
}

const CLE_STOCKAGE = 'rivdinde.session'

export const useAuthentification = defineStore('authentification', () => {
  const utilisateur = ref<Utilisateur | null>(null)
  const profil = ref<Record<string, unknown> | null>(null)
  const acces = ref<string | null>(null)
  const rafraichissement = ref<string | null>(null)
  const chargement = ref(false)

  const estConnecte = computed(() => utilisateur.value !== null)
  const role = computed(() => utilisateur.value?.role ?? null)
  // Un vendeur ou un livreur qui attend sa validation se connecte, mais ne
  // voit que son ecran d'attente (contrat-api.md).
  const enAttenteDeValidation = computed(
    () => utilisateur.value?.statut_compte === 'EN_ATTENTE_VALIDATION',
  )

  function memoriser(identite: Identite) {
    utilisateur.value = identite.utilisateur
    profil.value = identite.profil
    acces.value = identite.acces
    rafraichissement.value = identite.rafraichissement
    poserJeton(identite.acces)
    // Le televersement multipart passe par `fetch` brut, hors du client
    // commun : il lui faut le jeton, lui aussi.
    poserJetonVendeur(identite.acces)
    localStorage.setItem(
      CLE_STOCKAGE,
      JSON.stringify({ acces: identite.acces, rafraichissement: identite.rafraichissement }),
    )
  }

  async function restaurer() {
    const brut = localStorage.getItem(CLE_STOCKAGE)
    if (!brut) return
    try {
      const { acces: a, rafraichissement: r } = JSON.parse(brut)
      poserJeton(a)
      poserJetonVendeur(a)
      acces.value = a
      rafraichissement.value = r
      const donnees = await api.get<{ utilisateur: Utilisateur; profil: never }>('/moi')
      utilisateur.value = donnees.utilisateur
      profil.value = donnees.profil
    } catch {
      // Jeton expire ou revoque : on repart proprement plutot que de laisser
      // l'application dans un etat a moitie connecte.
      deconnecter()
    }
  }

  async function connecter(email: string, motDePasse: string) {
    chargement.value = true
    try {
      memoriser(await api.post<Identite>('/auth/connexion', { email, mot_de_passe: motDePasse }))
    } finally {
      chargement.value = false
    }
  }

  async function inscrire(type: 'client' | 'vendeur' | 'livreur', donnees: object) {
    chargement.value = true
    try {
      memoriser(await api.post<Identite>(`/auth/inscription/${type}`, donnees))
    } finally {
      chargement.value = false
    }
  }

  function deconnecter() {
    utilisateur.value = null
    profil.value = null
    acces.value = null
    rafraichissement.value = null
    poserJeton(null)
    poserJetonVendeur(null)
    localStorage.removeItem(CLE_STOCKAGE)
  }

  return {
    utilisateur, profil, chargement,
    estConnecte, role, enAttenteDeValidation,
    connecter, inscrire, deconnecter, restaurer,
  }
})
