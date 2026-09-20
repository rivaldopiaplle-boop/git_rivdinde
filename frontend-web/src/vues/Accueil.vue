<script setup lang="ts">
// Le tableau de bord de chaque role. A la tranche 1, il montre ce qui existe
// deja — l'identite, l'etat du systeme — et annonce ce qui vient. C'est un
// etat vide assume, pas une page oubliee.
import { Activity, ArrowRight, CircleCheck, CircleX, Server, UserRound } from '@lucide/vue'
import { computed, onMounted, ref } from 'vue'

import { api } from '../api/client'
import Squelette from '../composants/Squelette.vue'
import { descriptionDuRole } from '../roles'
import { useAuthentification } from '../stores/authentification'

const session = useAuthentification()
const role = computed(() => descriptionDuRole(session.role))

type Sante = { statut: string; version: string; base_de_donnees: string; environnement: string }
const sante = ref<Sante | null>(null)
const chargement = ref(true)

onMounted(async () => {
  try {
    sante.value = await api.get<Sante>('/sante')
  } catch {
    sante.value = null
  } finally {
    chargement.value = false
  }
})

const aVenir = computed(() => role.value.navigation.filter((entree) => entree.prochainement))
</script>

<template>
  <div class="mx-auto max-w-[1100px] animate-[apparition_0.2s_ease-out]">
    <!-- Tuiles de synthese : la forme qu'auront les vrais indicateurs des que
         les commandes existeront. -->
    <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      <article class="rounded-2xl border border-slate-200 bg-white p-5">
        <div class="flex items-center gap-3">
          <span
            class="flex h-10 w-10 items-center justify-center rounded-xl"
            :style="{ background: role.accentDoux, color: role.accent }"
          >
            <UserRound :size="19" />
          </span>
          <div class="min-w-0">
            <p class="text-[11px] tracking-wider text-slate-500 uppercase">Compte</p>
            <b class="block truncate text-[15px]">
              {{ session.utilisateur?.prenom }} {{ session.utilisateur?.nom }}
            </b>
          </div>
        </div>
        <dl class="mt-4 grid grid-cols-[auto_1fr] gap-x-4 gap-y-2 text-[13px]">
          <dt class="text-slate-500">Adresse</dt>
          <dd class="truncate font-medium">{{ session.utilisateur?.email }}</dd>
          <dt class="text-slate-500">Role</dt>
          <dd class="font-medium">{{ session.utilisateur?.role }}</dd>
          <dt class="text-slate-500">Statut</dt>
          <dd>
            <span
              class="inline-flex items-center gap-1.5 rounded-full bg-emerald-50 px-2 py-0.5
                     text-[12px] font-semibold text-emerald-700"
            >
              <CircleCheck :size="13" /> {{ session.utilisateur?.statut_compte }}
            </span>
          </dd>
        </dl>
      </article>

      <article class="rounded-2xl border border-slate-200 bg-white p-5">
        <div class="flex items-center gap-3">
          <span
            class="flex h-10 w-10 items-center justify-center rounded-xl bg-slate-100 text-slate-600"
          >
            <Server :size="19" />
          </span>
          <div>
            <p class="text-[11px] tracking-wider text-slate-500 uppercase">Systeme</p>
            <b class="text-[15px]">Etat de l'API</b>
          </div>
        </div>

        <div class="mt-4 flex flex-col gap-2 text-[13px]">
          <template v-if="chargement">
            <Squelette hauteur="0.9rem" largeur="70%" />
            <Squelette hauteur="0.9rem" largeur="45%" />
          </template>
          <template v-else-if="sante">
            <span class="inline-flex items-center gap-2 font-medium text-emerald-700">
              <CircleCheck :size="15" /> API {{ sante.statut }}
            </span>
            <span class="text-slate-500">
              version {{ sante.version }} · base {{ sante.base_de_donnees }} ·
              {{ sante.environnement }}
            </span>
          </template>
          <span v-else class="inline-flex items-center gap-2 font-medium text-red-600">
            <CircleX :size="15" /> API injoignable
          </span>
        </div>
      </article>

      <article class="rounded-2xl border border-slate-200 bg-white p-5">
        <div class="flex items-center gap-3">
          <span
            class="flex h-10 w-10 items-center justify-center rounded-xl bg-slate-100 text-slate-600"
          >
            <Activity :size="19" />
          </span>
          <div>
            <p class="text-[11px] tracking-wider text-slate-500 uppercase">Avancement</p>
            <b class="text-[15px]">Tranche 1 sur 11</b>
          </div>
        </div>
        <div class="mt-5 h-2 overflow-hidden rounded-full bg-slate-100">
          <div
            class="h-full rounded-full transition-[width] duration-500"
            :style="{ width: '18%', background: role.accent }"
          />
        </div>
        <p class="mt-3 text-[12.5px] text-slate-500">
          Comptes, roles et droits. Chaque tranche est verifiee avant d'ouvrir la suivante.
        </p>
      </article>
    </div>

    <!-- Etat vide pense : on annonce ce qui arrive plutot que de laisser une
         page blanche qui ressemble a un bogue (scenario 0). -->
    <article class="mt-5 rounded-2xl border border-slate-200 bg-white p-6">
      <h2 class="text-[12px] font-bold tracking-[0.08em] uppercase" :style="{ color: role.accent }">
        Ce qui arrive dans cet espace
      </h2>
      <ul class="mt-4 grid gap-2 sm:grid-cols-2">
        <li
          v-for="entree in aVenir"
          :key="entree.libelle"
          class="flex items-center gap-3 rounded-xl border border-slate-100 bg-slate-50/60 px-4 py-3"
        >
          <component :is="entree.icone" :size="17" class="shrink-0 text-slate-400" />
          <span class="text-[13.5px] font-medium">{{ entree.libelle }}</span>
          <ArrowRight :size="15" class="ml-auto text-slate-300" />
        </li>
      </ul>
    </article>
  </div>
</template>
