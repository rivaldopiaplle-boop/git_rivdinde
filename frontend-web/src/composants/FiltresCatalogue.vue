<script setup lang="ts">
// Les filtres du catalogue, tels qu'ils vivent DANS la sidebar.
//
// Les compteurs viennent du serveur et decrivent ce qui est reellement
// visible : depuis Paris, « Plats » n'annonce plus 4 alors qu'aucun plat n'est
// livrable (D-35).
import { Bike, Package, Store, Tag } from '@lucide/vue'

import { useCatalogue } from '../stores/catalogue'

const catalogue = useCatalogue()

const SERVICES = [
  { cle: undefined, libelle: 'Tous', icone: Store },
  { cle: 'EXPRESS', libelle: 'Express', icone: Bike },
  { cle: 'STANDARD', libelle: 'Standard', icone: Package },
]
</script>

<template>
  <section>
    <b class="text-[10.5px] tracking-[0.09em] text-slate-500 uppercase">Service</b>
    <div class="mt-2 flex gap-1 rounded-xl bg-white/5 p-1">
      <button
        v-for="option in SERVICES"
        :key="option.libelle"
        type="button"
        class="flex flex-1 items-center justify-center gap-1.5 rounded-lg py-1.5 text-[12px]
               transition-colors duration-150"
        :class="
          catalogue.service === option.cle
            ? 'bg-white/12 font-semibold text-white'
            : 'text-slate-400 hover:text-slate-200'
        "
        @click="catalogue.service = option.cle; catalogue.charger()"
      >
        <component :is="option.icone" :size="13" />
        {{ option.libelle }}
      </button>
    </div>
  </section>

  <section v-for="groupe in catalogue.univers" :key="groupe.nom">
    <b class="flex items-center justify-between text-[10.5px] tracking-[0.09em]
              text-slate-500 uppercase">
      {{ groupe.nom }}
      <span class="text-[10px] normal-case">{{ groupe.nombre }}</span>
    </b>
    <div class="mt-2 flex flex-col gap-0.5">
      <button
        v-for="element in groupe.categories"
        :key="element.slug"
        type="button"
        class="flex items-center justify-between rounded-lg px-2.5 py-1.5 text-left text-[12.5px]
               transition-colors duration-150"
        :class="
          catalogue.categorie === element.slug
            ? 'bg-white/12 font-semibold text-white'
            : 'text-slate-400 hover:bg-white/6 hover:text-slate-200'
        "
        @click="catalogue.basculer('categorie', element.slug)"
      >
        <span class="flex items-center gap-2 truncate">
          <Tag :size="12" class="opacity-50" />
          {{ element.nom }}
        </span>
        <span class="text-[10.5px] opacity-60">{{ element.nombre }}</span>
      </button>
    </div>
  </section>

  <section v-if="catalogue.boutiques.length">
    <b class="text-[10.5px] tracking-[0.09em] text-slate-500 uppercase">Boutiques</b>
    <div class="mt-2 flex flex-col gap-0.5">
      <button
        v-for="element in catalogue.boutiques"
        :key="element.id"
        type="button"
        class="flex items-center justify-between rounded-lg px-2.5 py-1.5 text-left text-[12.5px]
               transition-colors duration-150"
        :class="
          catalogue.boutique === String(element.id)
            ? 'bg-white/12 font-semibold text-white'
            : 'text-slate-400 hover:bg-white/6 hover:text-slate-200'
        "
        @click="catalogue.basculer('boutique', String(element.id))"
      >
        <span class="flex items-center gap-2 truncate">
          <component
            :is="element.type_service === 'EXPRESS' ? Bike : Package"
            :size="12"
            class="opacity-50"
          />
          {{ element.nom }}
        </span>
        <span class="text-[10.5px] opacity-60">{{ element.nombre }}</span>
      </button>
    </div>
  </section>

  <button
    v-if="catalogue.filtreActif"
    type="button"
    class="rounded-lg border border-white/10 px-3 py-1.5 text-[12px] text-slate-400
           transition-colors hover:border-white/25 hover:text-slate-200"
    @click="catalogue.toutEffacer()"
  >
    Tout effacer
  </button>
</template>
