import { api } from './client'

export type ApercuCommande = {
  type_service: string
  boutiques: string[]
  articles: number
  montant_produits_centimes: number
  montant_livraison_centimes: number
}

export type LigneCommande = {
  id: number
  nom_produit_capture: string
  prix_unitaire_centimes: number
  quantite: number
  sous_total_centimes: number
  image: string
}

export type SousCommande = {
  id: number
  boutique: string
  statut_preparation: string
  libelle_statut: string
  montant_vendeur_centimes: number
  montant_commission_centimes: number
  lignes: LigneCommande[]
  numero_commande?: string
  type_service?: string
  date_commande?: string
  suites_possibles?: string[]
}

export type Commande = {
  id: number
  numero_commande: string
  type_service: string
  statut_actuel: string
  libelle_statut: string
  montant_produits_centimes: number
  montant_livraison_centimes: number
  montant_total_centimes: number
  date_commande: string
  date_livraison_estimee: string | null
  adresse: string
  boutiques: string[]
  sous_commandes: SousCommande[]
}

export const commandes = {
  apercu: () =>
    api.get<{ commandes: ApercuCommande[]; total_centimes: number }>('/panier/apercu-commandes'),
  creer: (corps: object) => api.post<Commande[]>('/commandes', corps),
  miennes: () => api.get<Commande[]>('/mes-commandes'),
  recues: () => api.get<SousCommande[]>('/vendeurs/commandes'),
  avancer: (id: number, statut: string) =>
    api.patch<SousCommande>(`/vendeurs/sous-commandes/${id}`, { statut }),
}
