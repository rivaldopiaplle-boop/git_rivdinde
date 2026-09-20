// Ce que chaque role voit, de quelle couleur, et sur quel support.
//
// Les cinq accents viennent de plan-organisation/04-maquettes/design-system.md
// § 2. Ils s'appliquent PARTOUT, catalogue public compris : c'est une regle
// d'or, et les usages des CMS ne la remplacent pas (D-36 precisee au bloc H-6).
import {
  Bell, Bike, Boxes, ClipboardList, FileClock, LayoutDashboard, MapPin, Package,
  Receipt, ScrollText, Settings, ShieldCheck, ShoppingBag, Store, Truck, Users,
} from '@lucide/vue'
import type { Component } from 'vue'

import type { Role } from './stores/authentification'

export type EntreeNavigation = {
  libelle: string
  icone: Component
  route?: string
  prochainement?: boolean
}

/** Un visiteur sans compte est un futur client : il en porte les couleurs. */
export type RoleAffiche = Role | 'VISITEUR'

type DescriptionRole = {
  espace: string
  accent: string
  accentDoux: string
  /** Ou ce role travaille reellement (bloc H-9). */
  plateforme: 'web' | 'mobile' | 'web+mobile'
  navigation: EntreeNavigation[]
}

const CATALOGUE: EntreeNavigation[] = [
  { libelle: 'Catalogue', icone: ShoppingBag, route: 'vitrine' },
  { libelle: 'Boutiques', icone: Store, route: 'boutiques' },
]

export const ROLES: Record<RoleAffiche, DescriptionRole> = {
  VISITEUR: {
    espace: 'Catalogue',
    accent: '#16a34a',
    accentDoux: '#e8f8ee',
    plateforme: 'web+mobile',
    navigation: [
      ...CATALOGUE,
      { libelle: 'Vendre ou livrer', icone: Users, route: 'rejoindre' },
    ],
  },
  CLIENT: {
    espace: 'Espace client',
    accent: '#16a34a',
    accentDoux: '#e8f8ee',
    plateforme: 'web+mobile',
    navigation: [
      ...CATALOGUE,
      { libelle: 'Mes commandes', icone: Receipt, route: 'mes-commandes' },
      { libelle: 'Mes adresses', icone: MapPin, prochainement: true },
      { libelle: 'Notifications', icone: Bell, prochainement: true },
    ],
  },
  VENDEUR: {
    espace: 'Espace vendeur',
    accent: '#2563eb',
    accentDoux: '#eaf0ff',
    plateforme: 'web',
    navigation: [
      { libelle: 'Tableau de bord', icone: LayoutDashboard, route: 'espace' },
      { libelle: 'Mon catalogue', icone: Package, route: 'vendeur-catalogue' },
      { libelle: 'Commandes recues', icone: ClipboardList, route: 'vendeur-commandes' },
      { libelle: 'Stock', icone: Boxes, route: 'vendeur-catalogue' },
      { libelle: 'Personnel', icone: Users, prochainement: true },
      { libelle: 'Le catalogue public', icone: ShoppingBag, route: 'vitrine' },
    ],
  },
  GESTIONNAIRE: {
    espace: 'Espace gestion',
    accent: '#0d9488',
    accentDoux: '#e6f7f4',
    plateforme: 'web',
    navigation: [
      { libelle: 'Tableau de bord', icone: LayoutDashboard, route: 'espace' },
      { libelle: 'A preparer', icone: ClipboardList, route: 'vendeur-commandes' },
      { libelle: 'Stock', icone: Boxes, route: 'vendeur-catalogue' },
    ],
  },
  LIVREUR: {
    espace: 'Espace livreur',
    accent: '#7c3aed',
    accentDoux: '#f3edff',
    // Le livreur travaille sur son telephone, une main sur le guidon : lui
    // faire un espace web complet serait du travail perdu (bloc H-9).
    plateforme: 'mobile',
    navigation: [
      { libelle: 'Tableau de bord', icone: LayoutDashboard, route: 'espace' },
      { libelle: 'Ma course', icone: Bike, prochainement: true },
      { libelle: 'Ma tournee', icone: Truck, prochainement: true },
      { libelle: 'Historique', icone: FileClock, prochainement: true },
    ],
  },
  ADMIN: {
    espace: 'Administration',
    accent: '#b91c1c',
    accentDoux: '#fdebe9',
    plateforme: 'web',
    navigation: [
      { libelle: 'Tableau de bord', icone: LayoutDashboard, route: 'espace' },
      { libelle: 'Validations', icone: ShieldCheck, route: 'admin-validations' },
      { libelle: 'Utilisateurs', icone: Users, prochainement: true },
      { libelle: "Journal d'audit", icone: ScrollText, prochainement: true },
      { libelle: 'Parametres', icone: Settings, prochainement: true },
      { libelle: 'Le catalogue public', icone: ShoppingBag, route: 'vitrine' },
    ],
  },
}

export function descriptionDuRole(role: Role | null) {
  return ROLES[(role ?? 'VISITEUR') as RoleAffiche] ?? ROLES.VISITEUR
}
