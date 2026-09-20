<script setup lang="ts">
// Deux enveloppes seulement, et c'est voulu :
//
//   pleine page   connexion, inscription, attente de validation
//   coquille      TOUT le reste — catalogue public compris
//
// Le bloc H-6 a tranche : les CMS decident de l'affichage du contenu et des
// animations, jamais de la structure. Il n'y a donc qu'une seule structure.
import { computed } from 'vue'
import { useRoute } from 'vue-router'

import CoquilleApp from './composants/CoquilleApp.vue'
import FiltresCatalogue from './composants/FiltresCatalogue.vue'

const route = useRoute()
const pleinePage = computed(() => route.meta.plein === true)
</script>

<template>
  <RouterView v-if="pleinePage" />

  <CoquilleApp v-else>
    <template #filtres>
      <FiltresCatalogue />
    </template>
    <RouterView />
  </CoquilleApp>
</template>
