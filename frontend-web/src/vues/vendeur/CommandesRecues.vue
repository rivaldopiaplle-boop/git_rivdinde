<script setup lang="ts">
// La file du vendeur : ce qu'il doit preparer.
//
// Les boutons d'action viennent du SERVEUR (`suites_possibles`) : le front
// n'a pas a connaitre la machine a etats, il affiche ce qu'on lui donne. C'est
// ce qui garantit qu'un vendeur ne saute jamais une etape.
import { Bike, ClipboardList, Package } from '@lucide/vue'
import { onMounted, ref } from 'vue'

import { commandes, type SousCommande } from '../../api/commandes'
import Squelette from '../../composants/Squelette.vue'

const liste = ref<SousCommande[]>([])
const chargement = ref(true)
const erreur = ref('')

const LIBELLES: Record<string, string> = {
  EN_PREPARATION: 'Commencer la preparation',
  PRETE: 'Marquer prete',
  EXPEDIEE: 'Expedier',
  ANNULEE: 'Annuler',
}

async function charger() {
  chargement.value = true
  try {
    liste.value = await commandes.recues()
  } finally {
    chargement.value = false
  }
}

onMounted(charger)

async function avancer(sous: SousCommande, statut: string) {
  erreur.value = ''
  try {
    const mise_a_jour = await commandes.avancer(sous.id, statut)
    Object.assign(sous, mise_a_jour)
  } catch (echec) {
    erreur.value = echec instanceof Error ? echec.message : 'Changement refuse.'
  }
}

const euros = (centimes: number) =>
  (centimes / 100).toLocaleString('fr-FR', { style: 'currency', currency: 'EUR' })
</script>

<template>
  <div class="mx-auto max-w-[960px] animate-[apparition_0.2s_ease-out]">
    <p v-if="erreur" class="mb-4 rounded-xl bg-red-50 px-4 py-3 text-[13px] text-red-700">
      {{ erreur }}
    </p>

    <div v-if="chargement" class="flex flex-col gap-3">
      <Squelette v-for="n in 3" :key="n" hauteur="130px" />
    </div>

    <div v-else-if="!liste.length"
         class="rounded-2xl border border-slate-200 bg-white px-6 py-16 text-center">
      <span
        class="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl"
        :style="{ background: 'var(--accent-doux)', color: 'var(--accent)' }"
      >
        <ClipboardList :size="24" />
      </span>
      <b class="mt-4 block text-[15px]">Aucune commande pour l instant</b>
      <p class="mt-1.5 text-[13.5px] text-slate-500">
        Les commandes de vos clients apparaitront ici, dans leur ordre d arrivee.
      </p>
    </div>

    <div v-else class="flex flex-col gap-4">
      <article
        v-for="sous in liste"
        :key="sous.id"
        class="rounded-2xl border border-slate-200 bg-white p-5"
      >
        <div class="flex flex-wrap items-start justify-between gap-3">
          <div class="flex items-center gap-3">
            <span
              class="flex h-10 w-10 items-center justify-center rounded-xl"
              :style="{ background: 'var(--accent-doux)', color: 'var(--accent)' }"
            >
              <component :is="sous.type_service === 'EXPRESS' ? Bike : Package" :size="19" />
            </span>
            <div>
              <b class="text-[14.5px]">{{ sous.numero_commande }}</b>
              <p class="text-[12.5px] text-slate-500">
                {{ sous.date_commande ? new Date(sous.date_commande).toLocaleString('fr-FR') : '' }}
              </p>
            </div>
          </div>

          <div class="text-right">
            <span class="rounded-full bg-slate-100 px-3 py-1 text-[12px] font-semibold
                         text-slate-700">
              {{ sous.libelle_statut }}
            </span>
            <p class="mt-1.5 text-[12.5px] text-slate-500">
              Vous touchez <b class="text-slate-800">{{ euros(sous.montant_vendeur_centimes) }}</b>
              · commission {{ euros(sous.montant_commission_centimes) }}
            </p>
          </div>
        </div>

        <ul class="mt-4 flex flex-col gap-2 border-t border-slate-100 pt-4">
          <li
            v-for="ligne in sous.lignes"
            :key="ligne.id"
            class="flex items-center gap-3 text-[13.5px]"
          >
            <img
              v-if="ligne.image"
              :src="ligne.image"
              :alt="ligne.nom_produit_capture"
              class="h-10 w-10 rounded-lg object-cover"
            />
            <span class="flex-1">{{ ligne.nom_produit_capture }}</span>
            <span class="text-slate-500">x{{ ligne.quantite }}</span>
            <b>{{ euros(ligne.sous_total_centimes) }}</b>
          </li>
        </ul>

        <!-- Les seules actions autorisees, telles que le serveur les donne -->
        <div v-if="sous.suites_possibles?.length" class="mt-4 flex flex-wrap gap-2">
          <button
            v-for="suite in sous.suites_possibles"
            :key="suite"
            type="button"
            class="rounded-xl px-4 py-2 text-[13px] font-semibold transition-opacity
                   hover:opacity-90"
            :class="suite === 'ANNULEE' ? 'bg-red-50 text-red-700' : 'text-white'"
            :style="suite === 'ANNULEE' ? undefined : { background: 'var(--accent)' }"
            @click="avancer(sous, suite)"
          >
            {{ LIBELLES[suite] ?? suite }}
          </button>
        </div>
        <p v-else class="mt-4 text-[12.5px] text-slate-500">
          Plus rien a faire de votre cote sur cette commande.
        </p>
      </article>
    </div>
  </div>
</template>
