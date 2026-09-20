<script setup lang="ts">
// Le catalogue du vendeur : une liste dense, avec des boutons-icones pour
// consulter et gerer (regle d'or n°6). C'est l'ecran ou il passe ses journees.
import {
  AlertTriangle, Eye, EyeOff, ImageOff, Package, Pencil, Plus, Search,
} from '@lucide/vue'
import { computed, onMounted, ref } from 'vue'

import type { Produit } from '../../composants/CarteProduit.vue'
import Squelette from '../../composants/Squelette.vue'
import { vendeur } from '../../api/vendeur'

const produits = ref<Produit[]>([])
const chargement = ref(true)
const filtre = ref('')

async function charger() {
  chargement.value = true
  try {
    produits.value = await vendeur.mesProduits()
  } finally {
    chargement.value = false
  }
}

onMounted(charger)

const visibles = computed(() =>
  produits.value.filter((produit) =>
    produit.nom.toLowerCase().includes(filtre.value.trim().toLowerCase()),
  ),
)

const euros = (centimes: number) =>
  (centimes / 100).toLocaleString('fr-FR', { style: 'currency', currency: 'EUR' })
</script>

<template>
  <div class="animate-[apparition_0.2s_ease-out]">
    <div class="mb-5 flex flex-wrap items-center justify-between gap-3">
      <div class="relative">
        <Search :size="16" class="absolute top-1/2 left-3 -translate-y-1/2 text-slate-400" />
        <input
          v-model="filtre"
          type="search"
          placeholder="Filtrer mes produits…"
          class="w-64 rounded-xl border border-slate-200 bg-white py-2 pr-3 pl-9 text-[13.5px]
                 focus:border-slate-300 focus:outline-none"
        />
      </div>

      <RouterLink
        :to="{ name: 'vendeur-nouveau' }"
        class="inline-flex items-center gap-2 rounded-xl px-4 py-2.5 text-[13.5px] font-semibold
               text-white transition-opacity duration-150 hover:opacity-90"
        :style="{ background: 'var(--accent)' }"
      >
        <Plus :size="16" />
        Nouveau produit
      </RouterLink>
    </div>

    <div v-if="chargement" class="flex flex-col gap-2">
      <Squelette v-for="n in 5" :key="n" hauteur="64px" />
    </div>

    <!-- Etat vide pense : un vendeur qui arrive sur une page blanche croit que
         l'application est cassee (scenario 0). -->
    <div
      v-else-if="!produits.length"
      class="flex flex-col items-center rounded-2xl border border-slate-200 bg-white px-6 py-16
             text-center"
    >
      <span
        class="flex h-14 w-14 items-center justify-center rounded-2xl"
        :style="{ background: 'var(--accent-doux)', color: 'var(--accent)' }"
      >
        <Package :size="24" />
      </span>
      <b class="mt-4 text-[15px]">Votre catalogue est vide</b>
      <p class="mt-1.5 max-w-[46ch] text-[13.5px] text-slate-500">
        Ajoutez votre premier produit : un nom, un prix, une photo. Il apparaitra
        aussitot au catalogue de vos clients.
      </p>
      <RouterLink
        :to="{ name: 'vendeur-nouveau' }"
        class="mt-5 inline-flex items-center gap-2 rounded-xl px-4 py-2.5 text-[13.5px]
               font-semibold text-white"
        :style="{ background: 'var(--accent)' }"
      >
        <Plus :size="16" />
        Ajouter un produit
      </RouterLink>
    </div>

    <div v-else class="overflow-hidden rounded-2xl border border-slate-200 bg-white">
      <table class="w-full text-[13.5px]">
        <thead>
          <tr class="border-b border-slate-200 text-left text-[11px] tracking-wider
                     text-slate-500 uppercase">
            <th class="px-4 py-3 font-semibold">Produit</th>
            <th class="px-4 py-3 font-semibold">Prix</th>
            <th class="px-4 py-3 font-semibold">Stock</th>
            <th class="px-4 py-3 font-semibold">Etat</th>
            <th class="px-4 py-3 text-right font-semibold">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="produit in visibles"
            :key="produit.id"
            class="border-b border-slate-100 transition-colors last:border-0 hover:bg-slate-50/70"
          >
            <td class="px-4 py-3">
              <div class="flex items-center gap-3">
                <img
                  v-if="produit.image"
                  :src="produit.image"
                  :alt="produit.nom"
                  class="h-11 w-11 rounded-lg object-cover"
                />
                <span
                  v-else
                  class="flex h-11 w-11 items-center justify-center rounded-lg bg-slate-100
                         text-slate-400"
                >
                  <ImageOff :size="16" />
                </span>
                <b class="font-semibold">{{ produit.nom }}</b>
              </div>
            </td>
            <td class="px-4 py-3 font-semibold">{{ euros(produit.prix_centimes) }}</td>
            <td class="px-4 py-3">
              <span
                v-if="!produit.disponible"
                class="inline-flex items-center gap-1.5 rounded-full bg-red-50 px-2 py-0.5
                       text-[12px] font-semibold text-red-700"
              >
                <AlertTriangle :size="12" /> Rupture
              </span>
              <span v-else class="text-slate-600">en stock</span>
            </td>
            <td class="px-4 py-3">
              <span class="text-slate-500">{{ produit.boutique.type_service }}</span>
            </td>
            <td class="px-4 py-3">
              <!-- Boutons-icones, avec infobulle : la regle d'or n°6 le demande,
                   et un bouton-icone sans libelle accessible est inutilisable
                   au lecteur d'ecran. -->
              <div class="flex items-center justify-end gap-1">
                <RouterLink
                  :to="{ name: 'produit', params: { id: produit.id } }"
                  class="flex h-8 w-8 items-center justify-center rounded-lg text-slate-500
                         transition-colors hover:bg-slate-100 hover:text-slate-900"
                  title="Voir la fiche publique"
                >
                  <Eye :size="16" />
                  <span class="sr-only">Voir la fiche publique</span>
                </RouterLink>
                <RouterLink
                  :to="{ name: 'vendeur-produit', params: { id: produit.id } }"
                  class="flex h-8 w-8 items-center justify-center rounded-lg text-slate-500
                         transition-colors hover:bg-slate-100 hover:text-slate-900"
                  title="Modifier"
                >
                  <Pencil :size="16" />
                  <span class="sr-only">Modifier</span>
                </RouterLink>
                <button
                  type="button"
                  class="flex h-8 w-8 items-center justify-center rounded-lg text-slate-500
                         transition-colors hover:bg-red-50 hover:text-red-600"
                  title="Retirer du catalogue"
                  @click="vendeur.masquer(produit.id).then(charger)"
                >
                  <EyeOff :size="16" />
                  <span class="sr-only">Retirer du catalogue</span>
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
