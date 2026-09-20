<script setup lang="ts">
// Le suivi client : une frise par commande, avec le vocabulaire du bon
// circuit — « en tournee » n'a aucun sens pour une commande Express.
import { Bike, CheckCircle2, Package, Receipt } from '@lucide/vue'
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'

import { commandes, type Commande } from '../../api/commandes'
import Squelette from '../../composants/Squelette.vue'

const route = useRoute()
const liste = ref<Commande[]>([])
const chargement = ref(true)

onMounted(async () => {
  try {
    liste.value = await commandes.miennes()
  } finally {
    chargement.value = false
  }
})

const euros = (centimes: number) =>
  (centimes / 100).toLocaleString('fr-FR', { style: 'currency', currency: 'EUR' })

// Le vocabulaire differe selon le circuit : le client d'un restaurant ne
// comprendrait pas « expediee vers l'entrepot ».
const ETAPES_EXPRESS = ['PAYEE', 'EN_PREPARATION', 'PRETE', 'EN_LIVRAISON', 'LIVREE']
const ETAPES_STANDARD = [
  'PAYEE', 'EN_PREPARATION', 'EXPEDIEE_ENTREPOT', 'RECUE_ENTREPOT', 'EN_TOURNEE', 'LIVREE',
]
const LIBELLES: Record<string, string> = {
  EN_ATTENTE_PAIEMENT: 'En attente de paiement',
  PAYEE: 'Payee',
  EN_PREPARATION: 'En preparation',
  PRETE: 'Prete',
  EXPEDIEE_ENTREPOT: 'Vers l entrepot',
  RECUE_ENTREPOT: 'A l entrepot',
  EN_TOURNEE: 'En tournee',
  EN_LIVRAISON: 'En livraison',
  LIVREE: 'Livree',
}

function etapes(commande: Commande) {
  return commande.type_service === 'EXPRESS' ? ETAPES_EXPRESS : ETAPES_STANDARD
}
function position(commande: Commande) {
  return etapes(commande).indexOf(commande.statut_actuel)
}
</script>

<template>
  <div class="mx-auto max-w-[900px] animate-[apparition_0.2s_ease-out]">
    <p
      v-if="route.query.creees"
      class="mb-5 flex items-center gap-2 rounded-xl bg-emerald-50 px-4 py-3 text-[13.5px]
             text-emerald-800"
    >
      <CheckCircle2 :size="16" />
      {{ route.query.creees }} commande{{ Number(route.query.creees) > 1 ? 's' : '' }} creee{{
        Number(route.query.creees) > 1 ? 's' : ''
      }}.
    </p>

    <div v-if="chargement" class="flex flex-col gap-3">
      <Squelette v-for="n in 3" :key="n" hauteur="120px" />
    </div>

    <div v-else-if="!liste.length"
         class="rounded-2xl border border-slate-200 bg-white px-6 py-16 text-center">
      <span
        class="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl"
        :style="{ background: 'var(--accent-doux)', color: 'var(--accent)' }"
      >
        <Receipt :size="24" />
      </span>
      <b class="mt-4 block text-[15px]">Aucune commande pour l instant</b>
      <RouterLink
        :to="{ name: 'vitrine' }"
        class="mt-5 inline-flex rounded-xl px-4 py-2.5 text-[13.5px] font-semibold text-white"
        :style="{ background: 'var(--accent)' }"
      >
        Voir le catalogue
      </RouterLink>
    </div>

    <div v-else class="flex flex-col gap-4">
      <article
        v-for="commande in liste"
        :key="commande.id"
        class="rounded-2xl border border-slate-200 bg-white p-5"
      >
        <div class="flex flex-wrap items-start justify-between gap-3">
          <div class="flex items-center gap-3">
            <span
              class="flex h-10 w-10 items-center justify-center rounded-xl"
              :style="{ background: 'var(--accent-doux)', color: 'var(--accent)' }"
            >
              <component :is="commande.type_service === 'EXPRESS' ? Bike : Package" :size="19" />
            </span>
            <div>
              <b class="text-[14.5px]">{{ commande.numero_commande }}</b>
              <p class="text-[12.5px] text-slate-500">
                {{ commande.boutiques.join(' · ') }} ·
                {{ new Date(commande.date_commande).toLocaleDateString('fr-FR') }}
              </p>
            </div>
          </div>
          <b class="text-[16px]">{{ euros(commande.montant_total_centimes) }}</b>
        </div>

        <!-- La frise : on voit ou en est la commande, et ce qui reste -->
        <ol class="mt-5 flex items-center gap-1">
          <li
            v-for="(etape, index) in etapes(commande)"
            :key="etape"
            class="flex flex-1 flex-col gap-1.5"
          >
            <span
              class="h-1.5 rounded-full transition-colors"
              :style="{
                background: index <= position(commande) ? 'var(--accent)' : '#e2e8f0',
              }"
            />
            <span
              class="text-[10.5px]"
              :class="index <= position(commande) ? 'font-semibold text-slate-700' : 'text-slate-400'"
            >
              {{ LIBELLES[etape] }}
            </span>
          </li>
        </ol>

        <div class="mt-5 flex flex-col gap-2 border-t border-slate-100 pt-4">
          <div
            v-for="sous in commande.sous_commandes"
            :key="sous.id"
            class="flex items-center justify-between text-[13px]"
          >
            <span class="text-slate-600">{{ sous.boutique }}</span>
            <span class="rounded-full bg-slate-100 px-2.5 py-0.5 text-[11.5px] text-slate-600">
              {{ sous.libelle_statut }}
            </span>
          </div>
        </div>
      </article>
    </div>
  </div>
</template>
