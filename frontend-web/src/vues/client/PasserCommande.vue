<script setup lang="ts">
// Le tunnel de commande.
//
// Il montre le decoupage AVANT de valider : un client doit savoir qu'il cree
// trois commandes livrees separement (D-10). Le decouvrir apres le paiement
// serait une mauvaise surprise, et c'est exactement ce que les plateformes
// serieuses evitent.
import { ArrowRight, Bike, MapPin, Package, ShieldCheck } from '@lucide/vue'
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import { EchecApi } from '../../api/client'
import { commandes, type ApercuCommande } from '../../api/commandes'
import Squelette from '../../composants/Squelette.vue'
import { useAuthentification } from '../../stores/authentification'
import { usePanier } from '../../stores/panier'

const session = useAuthentification()
const panier = usePanier()
const routeur = useRouter()

const apercu = ref<ApercuCommande[]>([])
const total = ref(0)
const chargement = ref(true)
const erreur = ref('')
const envoi = ref(false)

const adresse = ref({ rue: '', code_postal: '', ville: '', instructions_livraison: '' })

onMounted(async () => {
  try {
    const donnees = await commandes.apercu()
    apercu.value = donnees.commandes
    total.value = donnees.total_centimes
  } catch (echec) {
    erreur.value = echec instanceof EchecApi ? echec.erreur.message : 'Panier indisponible.'
  } finally {
    chargement.value = false
  }
})

const euros = (centimes: number) =>
  (centimes / 100).toLocaleString('fr-FR', { style: 'currency', currency: 'EUR' })

const adresseRemplie = computed(
  () => adresse.value.rue.trim() && adresse.value.ville.trim() && adresse.value.code_postal.trim(),
)

async function valider() {
  erreur.value = ''
  envoi.value = true
  try {
    const creees = await commandes.creer(
      adresseRemplie.value ? { adresse: adresse.value } : {},
    )
    await panier.charger()
    routeur.push({ name: 'mes-commandes', query: { creees: creees.length } })
  } catch (echec) {
    erreur.value = echec instanceof EchecApi ? echec.erreur.message : 'Commande impossible.'
  } finally {
    envoi.value = false
  }
}
</script>

<template>
  <div class="mx-auto max-w-[840px] animate-[apparition_0.2s_ease-out]">
    <h2 class="text-[21px] font-semibold tracking-tight">Valider ma commande</h2>

    <div v-if="chargement" class="mt-5 flex flex-col gap-3">
      <Squelette hauteur="90px" />
      <Squelette hauteur="90px" />
    </div>

    <template v-else-if="apercu.length">
      <!-- Le decoupage, annonce avant tout engagement -->
      <p class="mt-2 text-[13.5px] text-slate-600">
        Votre panier donnera
        <b>{{ apercu.length }} commande{{ apercu.length > 1 ? 's' : '' }}</b>
        <template v-if="apercu.length > 1">
          , livrees separement — un seul paiement, plusieurs livraisons.
        </template>
      </p>

      <div class="mt-5 flex flex-col gap-3">
        <article
          v-for="(bloc, index) in apercu"
          :key="index"
          class="rounded-2xl border border-slate-200 bg-white p-5"
        >
          <div class="flex items-start justify-between gap-4">
            <div class="flex items-center gap-3">
              <span
                class="flex h-10 w-10 items-center justify-center rounded-xl"
                :style="{ background: 'var(--accent-doux)', color: 'var(--accent)' }"
              >
                <component :is="bloc.type_service === 'EXPRESS' ? Bike : Package" :size="19" />
              </span>
              <div>
                <b class="text-[14.5px]">
                  {{ bloc.type_service === 'EXPRESS' ? 'Livraison Express' : 'Livraison Standard' }}
                </b>
                <p class="text-[12.5px] text-slate-500">
                  {{ bloc.boutiques.join(' · ') }} — {{ bloc.articles }} article{{
                    bloc.articles > 1 ? 's' : ''
                  }}
                </p>
              </div>
            </div>
            <div class="text-right">
              <b class="text-[15px]">
                {{ euros(bloc.montant_produits_centimes + bloc.montant_livraison_centimes) }}
              </b>
              <p class="text-[12px] text-slate-500">
                dont
                {{
                  bloc.montant_livraison_centimes
                    ? euros(bloc.montant_livraison_centimes) + ' de livraison'
                    : 'livraison offerte'
                }}
              </p>
            </div>
          </div>
        </article>
      </div>

      <!-- Adresse -->
      <section class="mt-4 rounded-2xl border border-slate-200 bg-white p-5">
        <b class="flex items-center gap-2 text-[14px]">
          <MapPin :size="16" :style="{ color: 'var(--accent)' }" />
          Adresse de livraison
        </b>
        <p class="mt-1 text-[12.5px] text-slate-500">
          Laissez vide pour utiliser votre adresse principale.
        </p>
        <div class="mt-4 flex flex-wrap gap-3">
          <label class="flex min-w-[240px] flex-1 flex-col gap-1.5">
            <span class="text-[13px] text-slate-600">Rue</span>
            <input v-model="adresse.rue" class="champ-clair" />
          </label>
          <label class="flex w-32 flex-col gap-1.5">
            <span class="text-[13px] text-slate-600">Code postal</span>
            <input v-model="adresse.code_postal" class="champ-clair" />
          </label>
          <label class="flex min-w-[160px] flex-1 flex-col gap-1.5">
            <span class="text-[13px] text-slate-600">Ville</span>
            <input v-model="adresse.ville" class="champ-clair" />
          </label>
          <label class="flex w-full flex-col gap-1.5">
            <span class="text-[13px] text-slate-600">Instructions (code, etage…)</span>
            <input v-model="adresse.instructions_livraison" class="champ-clair" />
          </label>
        </div>
      </section>

      <p
        v-if="erreur"
        class="mt-4 rounded-xl bg-red-50 px-4 py-3 text-[13px] text-red-700"
      >
        {{ erreur }}
      </p>

      <!-- Total et validation -->
      <div class="mt-4 flex flex-wrap items-center justify-between gap-4 rounded-2xl border
                  border-slate-200 bg-white p-5">
        <div>
          <p class="text-[12.5px] text-slate-500">Total a payer</p>
          <b class="text-[26px]" :style="{ color: 'var(--accent)' }">{{ euros(total) }}</b>
        </div>

        <div class="flex flex-col items-end gap-2">
          <button
            v-if="session.estConnecte"
            type="button"
            class="inline-flex items-center gap-2 rounded-xl px-5 py-3 text-[14px] font-semibold
                   text-white transition-opacity hover:opacity-90 disabled:opacity-60"
            :style="{ background: 'var(--accent)' }"
            :disabled="envoi"
            @click="valider"
          >
            {{ envoi ? 'Validation…' : 'Valider ma commande' }}
            <ArrowRight :size="17" />
          </button>

          <RouterLink
            v-else
            :to="{ name: 'connexion' }"
            class="inline-flex items-center gap-2 rounded-xl px-5 py-3 text-[14px] font-semibold
                   text-white"
            :style="{ background: 'var(--accent)' }"
          >
            Se connecter pour commander
            <ArrowRight :size="17" />
          </RouterLink>

          <p class="flex items-center gap-1.5 text-[11.5px] text-slate-500">
            <ShieldCheck :size="13" />
            Le paiement Stripe arrive a la tranche suivante — la commande est creee sans
            debit.
          </p>
        </div>
      </div>
    </template>

    <div
      v-else
      class="mt-5 rounded-2xl border border-slate-200 bg-white px-6 py-16 text-center"
    >
      <b class="text-[15px]">Votre panier est vide</b>
      <p class="mt-1.5 text-[13.5px] text-slate-500">
        Ajoutez des articles au catalogue pour passer commande.
      </p>
      <RouterLink
        :to="{ name: 'vitrine' }"
        class="mt-5 inline-flex rounded-xl px-4 py-2.5 text-[13.5px] font-semibold text-white"
        :style="{ background: 'var(--accent)' }"
      >
        Voir le catalogue
      </RouterLink>
    </div>
  </div>
</template>
