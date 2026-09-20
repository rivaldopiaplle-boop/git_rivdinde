<script setup lang="ts">
// L'ecran qui debloque toute la plateforme : sans validation, un vendeur ne
// publie rien et un livreur ne livre rien (D-02).
import { Bike, Check, ShieldCheck, Store, X } from '@lucide/vue'
import { onMounted, ref } from 'vue'

import { api } from '../../api/client'
import Squelette from '../../composants/Squelette.vue'

type Candidat = {
  id: number
  nom_boutique?: string
  mode_livraison?: string
  vehicule?: string
  type_activite?: string
  utilisateur: { prenom: string; nom: string; email: string; date_inscription: string }
}

const vendeurs = ref<Candidat[]>([])
const livreurs = ref<Candidat[]>([])
const chargement = ref(true)
const message = ref('')

async function charger() {
  chargement.value = true
  try {
    const donnees = await api.get<{ vendeurs: Candidat[]; livreurs: Candidat[] }>(
      '/admin/validations',
    )
    vendeurs.value = donnees.vendeurs
    livreurs.value = donnees.livreurs
  } finally {
    chargement.value = false
  }
}

onMounted(charger)

async function decider(genre: 'vendeurs' | 'livreurs', id: number, action: string) {
  await api.post(`/admin/${genre}/${id}/${action}`)
  message.value =
    action === 'valider' ? 'Compte valide : il peut travailler.' : 'Candidature rejetee.'
  charger()
}
</script>

<template>
  <div class="mx-auto max-w-[900px] animate-[apparition_0.2s_ease-out]">
    <p v-if="message" class="mb-4 rounded-xl bg-emerald-50 px-4 py-3 text-[13.5px]
                             text-emerald-800">
      {{ message }}
    </p>

    <div v-if="chargement" class="flex flex-col gap-3">
      <Squelette v-for="n in 3" :key="n" hauteur="86px" />
    </div>

    <template v-else>
      <section v-if="vendeurs.length || livreurs.length" class="flex flex-col gap-6">
        <div v-if="vendeurs.length">
          <h3 class="flex items-center gap-2 text-[15px] font-semibold">
            <Store :size="17" :style="{ color: 'var(--accent)' }" />
            Boutiques en attente ({{ vendeurs.length }})
          </h3>
          <div class="mt-3 flex flex-col gap-2">
            <article
              v-for="candidat in vendeurs"
              :key="candidat.id"
              class="flex flex-wrap items-center justify-between gap-3 rounded-2xl border
                     border-slate-200 bg-white p-4"
            >
              <div>
                <b class="text-[14.5px]">{{ candidat.nom_boutique }}</b>
                <p class="text-[12.5px] text-slate-500">
                  {{ candidat.utilisateur.prenom }} {{ candidat.utilisateur.nom }} ·
                  {{ candidat.utilisateur.email }} · {{ candidat.type_activite }}
                </p>
              </div>
              <div class="flex gap-2">
                <button
                  type="button"
                  class="inline-flex items-center gap-1.5 rounded-xl px-4 py-2 text-[13px]
                         font-semibold text-white"
                  :style="{ background: 'var(--accent)' }"
                  @click="decider('vendeurs', candidat.id, 'valider')"
                >
                  <Check :size="15" /> Valider
                </button>
                <button
                  type="button"
                  class="inline-flex items-center gap-1.5 rounded-xl bg-slate-100 px-4 py-2
                         text-[13px] text-slate-700 hover:bg-slate-200"
                  @click="decider('vendeurs', candidat.id, 'rejeter')"
                >
                  <X :size="15" /> Rejeter
                </button>
              </div>
            </article>
          </div>
        </div>

        <div v-if="livreurs.length">
          <h3 class="flex items-center gap-2 text-[15px] font-semibold">
            <Bike :size="17" :style="{ color: 'var(--accent)' }" />
            Livreurs en attente ({{ livreurs.length }})
          </h3>
          <div class="mt-3 flex flex-col gap-2">
            <article
              v-for="candidat in livreurs"
              :key="candidat.id"
              class="flex flex-wrap items-center justify-between gap-3 rounded-2xl border
                     border-slate-200 bg-white p-4"
            >
              <div>
                <b class="text-[14.5px]">
                  {{ candidat.utilisateur.prenom }} {{ candidat.utilisateur.nom }}
                </b>
                <p class="text-[12.5px] text-slate-500">
                  {{ candidat.mode_livraison }} · {{ candidat.vehicule }} ·
                  {{ candidat.utilisateur.email }}
                </p>
              </div>
              <button
                type="button"
                class="inline-flex items-center gap-1.5 rounded-xl px-4 py-2 text-[13px]
                       font-semibold text-white"
                :style="{ background: 'var(--accent)' }"
                @click="decider('livreurs', candidat.id, 'valider')"
              >
                <Check :size="15" /> Valider
              </button>
            </article>
          </div>
        </div>
      </section>

      <div v-else class="rounded-2xl border border-slate-200 bg-white px-6 py-16 text-center">
        <span
          class="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl"
          :style="{ background: 'var(--accent-doux)', color: 'var(--accent)' }"
        >
          <ShieldCheck :size="24" />
        </span>
        <b class="mt-4 block text-[15px]">Rien en attente</b>
        <p class="mt-1.5 text-[13.5px] text-slate-500">
          Toutes les candidatures ont ete traitees.
        </p>
      </div>
    </template>
  </div>
</template>
