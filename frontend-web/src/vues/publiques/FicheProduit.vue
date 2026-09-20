<script setup lang="ts">
// La fiche produit : galerie, prix, boutique, disponibilite, ajout au panier.
//
// En rupture, le bouton est GELE et double d'une alerte de retour en stock
// (D-06) : le produit reste au catalogue, sinon on perd le client au lieu de
// le faire patienter.
import { ArrowLeft, Bike, Bell, Clock, MapPin, Package, ShieldCheck, ShoppingCart } from '@lucide/vue'
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'

import { catalogue, type ProduitDetail } from '../../api/catalogue'
import Squelette from '../../composants/Squelette.vue'
import { usePanier } from '../../stores/panier'
import { usePosition } from '../../stores/position'

const route = useRoute()
const position = usePosition()
const panier = usePanier()

const produit = ref<ProduitDetail | null>(null)
const chargement = ref(true)
const introuvable = ref(false)
const photoActive = ref(0)

async function charger() {
  chargement.value = true
  introuvable.value = false
  try {
    produit.value = await catalogue.produit(route.params.id as string, position.parametres)
    photoActive.value = 0
  } catch {
    introuvable.value = true
  } finally {
    chargement.value = false
  }
}

onMounted(charger)
watch(() => route.params.id, charger)

const prix = computed(() =>
  produit.value
    ? (produit.value.prix_centimes / 100).toLocaleString('fr-FR', {
        style: 'currency',
        currency: 'EUR',
      })
    : '',
)
const estExpress = computed(() => produit.value?.boutique?.type_service === 'EXPRESS')
// `photos?.length` et non `photos.length` : si la charge utile change de
// forme, l'ecran doit se degrader, pas planter toute l'application.
const photos = computed(() =>
  produit.value?.photos?.length ? produit.value.photos : produit.value?.image
    ? [{ id: 0, url: produit.value.image, texte_alternatif: produit.value.nom }]
    : [],
)
</script>

<template>
  <div class="mx-auto max-w-[1240px] px-5 py-10">
    <RouterLink
      to="/"
      class="inline-flex items-center gap-2 text-[13.5px] text-[#b49a8c] transition-colors
             hover:text-marque-clair"
    >
      <ArrowLeft :size="15" />
      Retour au catalogue
    </RouterLink>

    <div v-if="chargement" class="mt-6 grid gap-10 lg:grid-cols-2">
      <Squelette hauteur="420px" />
      <div class="flex flex-col gap-4">
        <Squelette hauteur="2rem" largeur="70%" />
        <Squelette hauteur="1rem" largeur="40%" />
        <Squelette hauteur="6rem" />
      </div>
    </div>

    <div
      v-else-if="introuvable"
      class="mt-10 rounded-2xl border border-encre-3 bg-encre-2/30 px-6 py-16 text-center"
    >
      <b class="text-[16px] text-white">Ce produit n'est plus au catalogue</b>
      <p class="mt-2 text-[13.5px] text-[#b49a8c]">
        Il a peut-etre ete retire par sa boutique, ou celle-ci ne livre pas votre ville.
      </p>
    </div>

    <article v-else-if="produit" class="mt-6 grid gap-10 lg:grid-cols-2">
      <!-- Galerie : grande image, vignettes dessous — le premier reflexe d'un
           acheteur (design-system.md § 9). -->
      <div>
        <div class="overflow-hidden rounded-2xl border border-encre-3 bg-encre-2">
          <img
            v-if="photos.length"
            :src="photos[photoActive]?.url"
            :alt="photos[photoActive]?.texte_alternatif"
            class="aspect-4/3 w-full object-cover"
          />
        </div>
        <div v-if="photos.length > 1" class="mt-3 flex gap-3">
          <button
            v-for="(photo, index) in photos"
            :key="photo.id"
            type="button"
            class="h-20 w-24 overflow-hidden rounded-xl border transition-colors duration-150"
            :class="index === photoActive ? 'border-marque' : 'border-encre-3 hover:border-marque/50'"
            @click="photoActive = index"
          >
            <img :src="photo.url" :alt="photo.texte_alternatif" class="h-full w-full object-cover" />
          </button>
        </div>
      </div>

      <div>
        <div class="flex items-center gap-2">
          <span
            class="flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[11.5px] font-semibold"
            :class="estExpress ? 'bg-amber-500/15 text-amber-300' : 'bg-slate-500/15 text-slate-300'"
          >
            <component :is="estExpress ? Bike : Package" :size="12" />
            {{ estExpress ? 'Livraison Express' : 'Livraison Standard' }}
          </span>
          <span v-if="produit.categorie" class="text-[12.5px] text-[#7c6459]">
            {{ produit.categorie.nom }}
          </span>
        </div>

        <h1 class="mt-4 text-[30px] leading-tight font-semibold tracking-tight text-white">
          {{ produit.nom }}
        </h1>

        <p class="mt-2 flex items-center gap-2 text-[13.5px] text-[#b49a8c]">
          <MapPin :size="14" />
          {{ produit.boutique?.nom }} · {{ produit.boutique?.ville }}
          <template v-if="produit.distance_km"> · {{ produit.distance_km }} km</template>
        </p>

        <p class="mt-6 text-[32px] font-bold text-marque">{{ prix }}</p>

        <p class="mt-5 text-[14.5px] leading-relaxed text-[#c9b4a6]">
          {{ produit.description }}
        </p>

        <!-- Disponibilite : bouton gele plutot que masque, avec l'alerte de
             retour en stock (D-06). -->
        <div class="mt-7 flex flex-col gap-3">
          <button
            v-if="produit.disponible"
            type="button"
            class="bouton-marque w-full"
            :disabled="panier.occupe"
            @click="panier.ajouter(produit.id)"
          >
            <ShoppingCart :size="17" />
            {{ panier.occupe ? 'Ajout…' : 'Ajouter au panier' }}
          </button>
          <template v-else>
            <button type="button" class="bouton-marque w-full cursor-not-allowed opacity-40" disabled>
              <ShoppingCart :size="17" />
              Indisponible
            </button>
            <button type="button" class="bouton-discret w-full">
              <Bell :size="15" />
              Etre alerte quand ce produit revient
            </button>
          </template>

          <p class="text-center text-[12px] text-[#7c6459]">
            Le paiement arrive a la tranche 5. Le panier, lui, fonctionne — et il vous suit
            si vous creez un compte ensuite.
          </p>
        </div>

        <ul class="mt-8 flex flex-col gap-3 border-t border-encre-3 pt-6">
          <li class="flex items-center gap-3 text-[13.5px] text-[#b49a8c]">
            <Clock :size="16" class="text-marque" />
            <template v-if="estExpress">Prepare et livre directement, en minutes.</template>
            <template v-else>Regroupe en entrepot, livre en tournee sous 48 a 72 heures.</template>
          </li>
          <li class="flex items-center gap-3 text-[13.5px] text-[#b49a8c]">
            <ShieldCheck :size="16" class="text-marque" />
            Boutique verifiee par la plateforme avant publication.
          </li>
        </ul>
      </div>
    </article>
  </div>
</template>
