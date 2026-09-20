<script setup lang="ts">
// Deux objets, pas un seul — c'est la regle de toute marque a mascotte :
//
//   variante="complet"  la mascotte, pour les grandes surfaces (accueil,
//                       ecran de demarrage, page de connexion). Riche, mais
//                       illisible en dessous de ~96 px.
//   variante="symbole"  le monogramme R en SVG, pour la navbar, les listes,
//                       l'onglet du navigateur. Net a 16 px, aucun octet a
//                       telecharger.
//
// Reference : plan-organisation/04-maquettes/identite-visuelle.html
withDefaults(
  defineProps<{ taille?: number; variante?: 'complet' | 'symbole' }>(),
  { taille: 40, variante: 'symbole' },
)

// Chemins construits a l'execution plutot qu'ecrits en dur dans l'attribut :
// Vite tente sinon de resoudre `/logo-…webp` comme un module a la compilation,
// ce qui fait echouer les tests unitaires. Le fichier est servi tel quel depuis
// `public/`, le resultat est identique dans le navigateur.
const SOURCE = '/logo-rivdinde-512.webp'
const SOURCES = [
  '/logo-rivdinde-192.webp 192w',
  '/logo-rivdinde-256.webp 256w',
  '/logo-rivdinde-512.webp 512w',
].join(', ')
</script>

<template>
  <!-- La mascotte est servie en WebP, avec trois tailles : le navigateur
       prend celle qui correspond a son ecran au lieu de charger la plus
       grande et de la reduire. -->
  <img
    v-if="variante === 'complet'"
    :width="taille"
    :height="taille"
    :src="SOURCE"
    :srcset="SOURCES"
    :sizes="`${taille}px`"
    alt="RivDinde"
    class="marque-complete"
  />

  <svg
    v-else
    :width="taille"
    :height="taille"
    viewBox="0 0 64 64"
    role="img"
    aria-label="RivDinde"
  >
    <defs>
      <linearGradient :id="`fond${taille}`" x1="0" y1="0" x2="0.6" y2="1">
        <stop offset="0" stop-color="#3d2016" /><stop offset="1" stop-color="#2a160f" />
      </linearGradient>
      <linearGradient :id="`lettre${taille}`" x1="0" y1="0" x2="0.3" y2="1">
        <stop offset="0" stop-color="#f0a344" /><stop offset="1" stop-color="#d46f1d" />
      </linearGradient>
    </defs>
    <rect width="64" height="64" rx="15" :fill="`url(#fond${taille})`" />
    <g
      fill="none" :stroke="`url(#lettre${taille})`" stroke-width="9.5"
      stroke-linecap="round" stroke-linejoin="round"
    >
      <path d="M21 14 V47" />
      <path d="M21 14 H31 A10 10 0 0 1 31 36 H21" />
      <path d="M30 35 L42 47" />
    </g>
  </svg>
</template>

<style scoped>
.marque-complete {
  /* Le logo fourni a un fond opaque : on l'arrondit pour qu'il se pose sur
     n'importe quelle surface sans faire « image collee ». */
  border-radius: 18px;
  display: block;
}
</style>
