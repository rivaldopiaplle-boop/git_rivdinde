<script setup lang="ts">
// « Livrer a … » : le premier geste que fait un visiteur sur une plateforme
// de livraison. Tant qu'il n'a pas repondu, aucune boutique Express ne peut
// s'afficher — et le dire vaut mieux que d'afficher une page a moitie vide.
import { Crosshair, MapPin } from '@lucide/vue'
import { ref } from 'vue'

import { usePosition, VILLES, type Ville } from '../stores/position'

const position = usePosition()
const ouvert = ref(false)

function choisir(ville: Ville) {
  position.choisir(ville)
  ouvert.value = false
}
</script>

<template>
  <div class="relative">
    <button
      type="button"
      class="flex items-center gap-2 rounded-xl border border-encre-3 bg-encre-2/60 px-3 py-2
             text-[13px] transition-colors duration-150 hover:border-marque"
      @click="ouvert = !ouvert"
    >
      <MapPin :size="15" class="text-marque" />
      <span class="text-[#b49a8c]">Livrer a</span>
      <b class="text-white">{{ position.libelle }}</b>
    </button>

    <Transition
      enter-active-class="transition duration-150"
      enter-from-class="opacity-0 -translate-y-1"
      leave-active-class="transition duration-100"
      leave-to-class="opacity-0"
    >
      <div
        v-if="ouvert"
        class="absolute top-full left-0 z-50 mt-2 w-64 rounded-2xl border border-encre-3
               bg-encre-2 p-2 shadow-2xl shadow-black/40"
      >
        <button
          type="button"
          class="flex w-full items-center gap-2.5 rounded-xl px-3 py-2.5 text-left text-[13px]
                 text-marque-clair transition-colors hover:bg-white/5"
          @click="position.localiser()"
        >
          <Crosshair :size="15" />
          {{ position.localisationEnCours ? 'Localisation…' : 'Utiliser ma position' }}
        </button>

        <div class="my-1.5 border-t border-encre-3" />

        <button
          v-for="ville in VILLES"
          :key="ville.nom"
          type="button"
          class="flex w-full items-center justify-between rounded-xl px-3 py-2 text-left
                 text-[13.5px] transition-colors hover:bg-white/5"
          :class="position.ville?.nom === ville.nom ? 'text-marque' : 'text-[#c9b4a6]'"
          @click="choisir(ville)"
        >
          {{ ville.nom }}
          <span v-if="position.ville?.nom === ville.nom" class="text-[11px]">choisie</span>
        </button>
      </div>
    </Transition>
  </div>
</template>
