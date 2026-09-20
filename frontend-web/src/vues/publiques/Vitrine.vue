<script setup lang="ts">
// Le catalogue — la page d'accueil, publique (D-03 et D-33).
//
// Elle vit dans la coquille commune : sidebar de filtres a gauche, navbar en
// haut, panier a droite. Ce qu'elle apporte, c'est le contenu : la banniere et
// la grille. Le cadre, lui, est le meme partout (bloc H-6 et H-8).
import { ArrowRight, MapPin, Search, Store } from '@lucide/vue'
import { computed, onMounted, watch } from 'vue'

import CarteProduit from '../../composants/CarteProduit.vue'
import Squelette from '../../composants/Squelette.vue'
import { useCatalogue } from '../../stores/catalogue'
import { usePosition } from '../../stores/position'

const catalogue = useCatalogue()
const position = usePosition()

const MASCOTTE = '/logo-rivdinde-512.webp'

onMounted(() => {
  if (!catalogue.produits.length) catalogue.charger()
})
watch(() => position.parametres, () => catalogue.charger())

const titre = computed(() =>
  catalogue.recherche.trim() ? `Resultats pour « ${catalogue.recherche.trim()} »` : 'Le catalogue',
)
</script>

<template>
  <div class="mx-auto max-w-[1180px] animate-[apparition_0.2s_ease-out]">
    <!-- Banniere : le seul endroit ou le contenu marchand prend la parole. -->
    <section
      class="relative flex flex-col items-center gap-8 overflow-hidden rounded-2xl border
             border-slate-200 bg-white px-8 py-10 lg:flex-row lg:justify-between lg:py-12"
    >
      <div
        class="pointer-events-none absolute -top-24 -right-16 h-72 w-72 rounded-full blur-3xl"
        :style="{ background: 'var(--accent-doux)' }"
      />
      <div class="relative">
        <p class="text-[11.5px] font-bold tracking-[0.14em] uppercase"
           :style="{ color: 'var(--accent)' }">
          Commander, livrer, suivre
        </p>
        <h2 class="mt-3 max-w-[16ch] text-[34px] leading-[1.12] font-semibold tracking-tight">
          Deux rythmes, une seule plateforme.
        </h2>
        <p class="mt-4 max-w-[56ch] text-[14.5px] leading-relaxed text-slate-600">
          <b class="text-slate-900">Express</b> : les boutiques proches de chez vous, livrees
          directement. <b class="text-slate-900">Standard</b> : tout le catalogue, regroupe en
          entrepot et livre en tournee.
        </p>
        <div class="mt-6 flex flex-wrap gap-3">
          <a
            href="#grille"
            class="inline-flex items-center gap-2 rounded-xl px-4 py-2.5 text-[13.5px]
                   font-semibold text-white transition-opacity hover:opacity-90"
            :style="{ background: 'var(--accent)' }"
          >
            Voir le catalogue
            <ArrowRight :size="16" />
          </a>
          <RouterLink
            :to="{ name: 'rejoindre' }"
            class="inline-flex items-center gap-2 rounded-xl border border-slate-200 px-4 py-2.5
                   text-[13.5px] transition-colors hover:bg-slate-50"
          >
            <Store :size="15" />
            Vendre ou livrer
          </RouterLink>
        </div>
      </div>

      <img :src="MASCOTTE" alt="" class="mascotte relative w-[180px] rounded-3xl lg:w-[230px]" />
    </section>

    <p
      v-if="!position.connue"
      class="mt-4 flex items-center gap-2 rounded-xl border border-amber-200 bg-amber-50 px-4
             py-3 text-[13px] text-amber-900"
    >
      <MapPin :size="15" class="shrink-0" />
      Indiquez votre ville en haut de page pour voir aussi les boutiques Express proches —
      au-dela de leur rayon, elles ne peuvent pas vous livrer.
    </p>

    <section id="grille" class="scroll-mt-24 pt-8">
      <div class="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h3 class="text-[17px] font-semibold tracking-tight">{{ titre }}</h3>
          <p class="mt-0.5 text-[13px] text-slate-500">
            {{ catalogue.produits.length }} produit{{ catalogue.produits.length > 1 ? 's' : '' }}
            <template v-if="position.connue"> · livrable a {{ position.libelle }}</template>
          </p>
        </div>
      </div>

      <div v-if="catalogue.chargement" class="mt-5 grid gap-5 sm:grid-cols-2 xl:grid-cols-3">
        <div
          v-for="n in 6"
          :key="n"
          class="overflow-hidden rounded-2xl border border-slate-200 bg-white"
        >
          <Squelette hauteur="170px" />
          <div class="flex flex-col gap-2 p-4">
            <Squelette hauteur="0.9rem" largeur="80%" />
            <Squelette hauteur="0.8rem" largeur="50%" />
          </div>
        </div>
      </div>

      <div
        v-else-if="catalogue.produits.length"
        class="mt-5 grid gap-5 sm:grid-cols-2 xl:grid-cols-3"
      >
        <CarteProduit
          v-for="produit in catalogue.produits"
          :key="produit.id"
          :produit="produit"
        />
      </div>

      <div
        v-else
        class="mt-5 flex flex-col items-center rounded-2xl border border-slate-200 bg-white
               px-6 py-16 text-center"
      >
        <span
          class="flex h-14 w-14 items-center justify-center rounded-2xl"
          :style="{ background: 'var(--accent-doux)', color: 'var(--accent)' }"
        >
          <Search :size="24" />
        </span>
        <b class="mt-4 text-[15px]">Aucun produit ne correspond</b>
        <p class="mt-1.5 max-w-[46ch] text-[13.5px] text-slate-500">
          <template v-if="!position.connue && catalogue.service === 'EXPRESS'">
            Les boutiques Express n apparaissent qu une fois votre ville indiquee.
          </template>
          <template v-else>Retirez un filtre pour elargir le resultat.</template>
        </p>
        <button
          v-if="catalogue.filtreActif"
          type="button"
          class="mt-5 rounded-xl border border-slate-200 px-4 py-2 text-[13px]
                 transition-colors hover:bg-slate-50"
          @click="catalogue.toutEffacer()"
        >
          Tout effacer
        </button>
      </div>
    </section>
  </div>
</template>

<style scoped>
.mascotte {
  animation: flotter 5.5s ease-in-out infinite;
  filter: drop-shadow(0 18px 26px rgb(42 22 15 / 0.28));
  transform-origin: 50% 85%;
}

@keyframes flotter {
  0%,
  100% {
    transform: translateY(0) rotate(-1.2deg);
  }
  50% {
    transform: translateY(-12px) rotate(1.4deg);
  }
}

/* Certaines personnes ont mal au coeur devant une animation continue. */
@media (prefers-reduced-motion: reduce) {
  .mascotte {
    animation: none;
  }
}
</style>
