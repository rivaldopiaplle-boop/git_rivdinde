import { api, appelerComplet } from './client'
import type { Produit } from '../composants/CarteProduit.vue'

const BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api/v1'

export type Photo = { id: number; url: string; ordre: number; texte_alternatif: string }

export type ProduitVendeur = {
  id: number
  nom: string
  description: string
  prix_unitaire_centimes: number
  categorie: number | null
  poids_grammes: number | null
  stock_disponible: number
  seuil_alerte: number
  est_visible: boolean
  image_principale_url: string
}

export type Mouvement = {
  id: number
  type: string
  libelle_type: string
  quantite: number
  motif: string
  stock_apres: number
  date_mouvement: string
  auteur: string
}

let jetonCourant: string | null = null
export function poserJetonVendeur(jeton: string | null) {
  jetonCourant = jeton
}

/** Le televersement passe par `fetch` brut : un envoi multipart ne doit pas
 *  porter d'en-tete Content-Type fixe, le navigateur ecrit lui-meme la
 *  frontiere entre les fichiers. */
async function televerser(chemin: string, fichiers: File[]) {
  const corps = new FormData()
  for (const fichier of fichiers) corps.append('photos', fichier)

  const reponse = await fetch(`${BASE}${chemin}`, {
    method: 'POST',
    headers: jetonCourant ? { Authorization: `Bearer ${jetonCourant}` } : {},
    body: corps,
  })
  const donnees = await reponse.json().catch(() => null)
  if (!reponse.ok) {
    throw new Error(donnees?.erreur?.message ?? "Le televersement a echoue.")
  }
  return donnees.data as Photo[]
}

export const vendeur = {
  mesProduits: () => api.get<Produit[]>('/vendeurs/produits'),
  stockBas: () => api.get<Produit[]>('/vendeurs/stock-bas'),
  detail: (id: number | string) => appelerComplet<{ data: never }>(`/produits/${id}`),
  creer: (donnees: Partial<ProduitVendeur>) => api.post<never>('/vendeurs/produits', donnees),
  modifier: (id: number, donnees: Partial<ProduitVendeur>) =>
    api.patch<never>(`/vendeurs/produits/${id}`, donnees),
  masquer: (id: number) => api.supprimer<void>(`/vendeurs/produits/${id}`),

  photos: {
    ajouter: (id: number, fichiers: File[]) => televerser(`/produits/${id}/photos`, fichiers),
    ordonner: (id: number, ordre: number[]) =>
      api.patch<Photo[]>(`/produits/${id}/photos/ordre`, { ordre }),
    retirer: (id: number, idPhoto: number) =>
      api.supprimer<Photo[]>(`/produits/${id}/photos/${idPhoto}`),
  },

  stock: {
    ajuster: (id: number, quantite: number, type: string, motif: string) =>
      api.patch<{ stock_disponible: number; mouvement: Mouvement }>(`/produits/${id}/stock`, {
        quantite,
        type,
        motif,
      }),
    mouvements: (id: number) => api.get<Mouvement[]>(`/produits/${id}/mouvements`),
  },
}
