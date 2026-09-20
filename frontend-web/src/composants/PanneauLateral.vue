<script setup lang="ts">
// Le panneau de droite : **stable et retractable**, jamais une fenetre qui
// apparait puis disparait par-dessus la page (regle d'or n°6, precisee au
// bloc H-7). Replie, il reste visible sous forme de bande : le panier ne
// disparait pas de la vue, il se met de cote.
import { AlertTriangle, Bell, ChevronsRight, Minus, Plus, ShoppingCart, Trash2 } from '@lucide/vue'
import { computed } from 'vue'

import { usePanier } from '../stores/panier'

const panier = usePanier()

const euros = (centimes: number) =>
  (centimes / 100).toLocaleString('fr-FR', { style: 'currency', currency: 'EUR' })

const vide = computed(() => panier.contenu.lignes.length === 0)
</script>

<template>
  <aside
    class="hidden shrink-0 border-l border-slate-200 bg-white transition-[width] duration-200
           lg:flex lg:flex-col"
    :class="panier.ouvert ? 'w-[330px]' : 'w-[58px]'"
  >
    <!-- Bande repliee : le panier reste sous les yeux, avec son compteur. -->
    <div class="flex items-center gap-2 border-b border-slate-200 px-3 py-4"
         :class="panier.ouvert ? 'justify-between' : 'justify-center'">
      <button
        type="button"
        class="relative flex h-9 w-9 items-center justify-center rounded-xl text-slate-600
               transition-colors hover:bg-slate-100"
        :title="panier.ouvert ? 'Replier le panier' : 'Ouvrir le panier'"
        @click="panier.ouvert = !panier.ouvert"
      >
        <component :is="panier.ouvert ? ChevronsRight : ShoppingCart" :size="18" />
        <span
          v-if="!panier.ouvert && panier.nombreArticles"
          class="absolute -top-1 -right-1 flex h-[17px] min-w-[17px] items-center justify-center
                 rounded-full px-1 text-[10px] font-bold text-white"
          :style="{ background: 'var(--accent)' }"
        >
          {{ panier.nombreArticles }}
        </span>
      </button>

      <b v-if="panier.ouvert" class="flex-1 text-[14px]">Mon panier</b>
      <span
        v-if="panier.ouvert && panier.nombreArticles"
        class="rounded-full px-2 py-0.5 text-[11px] font-bold text-white"
        :style="{ background: 'var(--accent)' }"
      >
        {{ panier.nombreArticles }}
      </span>
    </div>

    <template v-if="panier.ouvert">
      <p
        v-if="panier.erreur"
        class="mx-4 mt-3 rounded-xl bg-red-50 px-3 py-2.5 text-[12.5px] text-red-700"
      >
        {{ panier.erreur }}
      </p>

      <div v-if="!vide" class="flex-1 overflow-y-auto px-4 py-3">
        <article
          v-for="ligne in panier.contenu.lignes"
          :key="ligne.id"
          class="flex gap-3 border-b border-slate-100 py-3 last:border-0"
        >
          <img
            v-if="ligne.produit.image"
            :src="ligne.produit.image"
            :alt="ligne.produit.nom"
            class="h-14 w-14 shrink-0 rounded-lg object-cover"
          />
          <div class="min-w-0 flex-1">
            <b class="block truncate text-[13px]">{{ ligne.produit.nom }}</b>
            <span class="text-[11.5px] text-slate-500">{{ ligne.produit.boutique.nom }}</span>

            <p
              v-if="ligne.prix_a_change"
              class="mt-0.5 flex items-center gap-1 text-[11px] text-amber-600"
            >
              <AlertTriangle :size="11" /> Prix modifie depuis l ajout
            </p>

            <div class="mt-1.5 flex items-center justify-between">
              <div class="flex items-center rounded-lg border border-slate-200">
                <button
                  type="button"
                  class="flex h-6 w-6 items-center justify-center text-slate-500 hover:text-slate-900"
                  :disabled="panier.occupe"
                  @click="panier.changerQuantite(ligne.id, ligne.quantite - 1)"
                >
                  <Minus :size="12" />
                </button>
                <span class="w-5 text-center text-[12.5px] font-semibold">{{ ligne.quantite }}</span>
                <button
                  type="button"
                  class="flex h-6 w-6 items-center justify-center text-slate-500
                         hover:text-slate-900 disabled:opacity-30"
                  :disabled="panier.occupe || ligne.quantite >= ligne.produit.stock_commandable"
                  @click="panier.changerQuantite(ligne.id, ligne.quantite + 1)"
                >
                  <Plus :size="12" />
                </button>
              </div>
              <div class="flex items-center gap-2">
                <b class="text-[13px]">{{ euros(ligne.sous_total_centimes) }}</b>
                <button
                  type="button"
                  class="text-slate-400 transition-colors hover:text-red-600"
                  title="Retirer"
                  @click="panier.retirer(ligne.id)"
                >
                  <Trash2 :size="14" />
                </button>
              </div>
            </div>
          </div>
        </article>
      </div>

      <div v-else class="flex flex-1 flex-col items-center justify-center px-6 text-center">
        <span
          class="flex h-12 w-12 items-center justify-center rounded-2xl"
          :style="{ background: 'var(--accent-doux)', color: 'var(--accent)' }"
        >
          <ShoppingCart :size="20" />
        </span>
        <b class="mt-3 text-[13.5px]">Panier vide</b>
        <p class="mt-1 text-[12.5px] text-slate-500">
          Aucun compte n est necessaire pour commencer.
        </p>
      </div>

      <div v-if="!vide" class="border-t border-slate-200 p-4">
        <p
          v-if="panier.plusieursBoutiques"
          class="mb-3 rounded-lg bg-slate-50 px-3 py-2 text-[11.5px] text-slate-600"
        >
          {{ panier.contenu.boutiques.length }} boutiques : plusieurs commandes livrees
          separement, un seul paiement.
        </p>
        <div class="flex items-center justify-between">
          <span class="text-[12.5px] text-slate-500">Total</span>
          <b class="text-[18px]" :style="{ color: 'var(--accent)' }">{{ panier.total }}</b>
        </div>
        <RouterLink
          :to="{ name: 'commande' }"
          class="mt-3 flex w-full items-center justify-center gap-2 rounded-xl px-4 py-2.5
                 text-[13.5px] font-semibold text-white transition-opacity hover:opacity-90"
          :style="{ background: 'var(--accent)' }"
        >
          Passer commande
        </RouterLink>
      </div>

      <div class="border-t border-slate-200 px-4 py-3">
        <p class="flex items-center gap-2 text-[11.5px] text-slate-400">
          <Bell :size="12" /> Les notifications s afficheront ici.
        </p>
      </div>
    </template>
  </aside>
</template>
