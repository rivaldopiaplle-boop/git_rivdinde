<script setup lang="ts">
// La liste des boutiques. Cliquer sur l'une d'elles filtre le catalogue —
// c'est le geste attendu, et il reutilise la facette « boutique » deja en
// place plutot que d'inventer un ecran de plus.
import { Bike, Package, Store } from '@lucide/vue'
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import { catalogue as apiCatalogue, type Boutique } from '../../api/catalogue'
import Squelette from '../../composants/Squelette.vue'
import { useCatalogue } from '../../stores/catalogue'
import { usePosition } from '../../stores/position'

const position = usePosition()
const catalogue = useCatalogue()
const routeur = useRouter()

const liste = ref<Boutique[]>([])
const chargement = ref(true)

onMounted(async () => {
  try {
    liste.value = await apiCatalogue.boutiques(position.parametres)
  } finally {
    chargement.value = false
  }
})

function voirLeCatalogue(boutique: Boutique) {
  catalogue.boutique = String(boutique.id)
  catalogue.charger()
  routeur.push({ name: 'vitrine' })
}
</script>

<template>
  <div class="mx-auto max-w-[1100px] animate-[apparition_0.2s_ease-out]">
    <div v-if="chargement" class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      <Squelette v-for="n in 3" :key="n" hauteur="150px" />
    </div>

    <div v-else-if="liste.length" class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      <button
        v-for="boutique in liste"
        :key="boutique.id"
        type="button"
        class="rounded-2xl border border-slate-200 bg-white p-5 text-left transition-all
               duration-200 hover:-translate-y-0.5 hover:shadow-lg"
        @click="voirLeCatalogue(boutique)"
      >
        <div class="flex items-start justify-between gap-3">
          <div>
            <b class="text-[15.5px]">{{ boutique.nom }}</b>
            <p class="mt-0.5 text-[12.5px] text-slate-500">
              {{ boutique.ville }}
              <template v-if="boutique.distance_km"> · {{ boutique.distance_km }} km</template>
            </p>
          </div>
          <span
            class="flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] font-semibold"
            :class="
              boutique.type_service === 'EXPRESS'
                ? 'bg-amber-50 text-amber-700'
                : 'bg-slate-100 text-slate-600'
            "
          >
            <component :is="boutique.type_service === 'EXPRESS' ? Bike : Package" :size="12" />
            {{ boutique.type_service === 'EXPRESS' ? 'Express' : 'Standard' }}
          </span>
        </div>
        <p class="mt-3 text-[13.5px] leading-relaxed text-slate-600">{{ boutique.description }}</p>
        <p class="mt-3 text-[12.5px] text-slate-400">
          {{ boutique.nombre_produits }} produit{{ boutique.nombre_produits > 1 ? 's' : '' }}
        </p>
      </button>
    </div>

    <div v-else class="rounded-2xl border border-slate-200 bg-white px-6 py-16 text-center">
      <span
        class="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl"
        :style="{ background: 'var(--accent-doux)', color: 'var(--accent)' }"
      >
        <Store :size="24" />
      </span>
      <b class="mt-4 block text-[15px]">Aucune boutique a afficher</b>
      <p class="mt-1.5 text-[13.5px] text-slate-500">
        Indiquez votre ville en haut de page pour voir les boutiques Express proches.
      </p>
    </div>
  </div>
</template>
