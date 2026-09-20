<script setup lang="ts">
// L'ecran d'attente de validation. Il existe parce qu'un vendeur qui se
// connecte et tombe sur un tableau de bord vide croit que l'application est
// cassee : chaque role a besoin d'un etat vide pense (scenario 0).
import { ArrowLeft, CheckCircle2, Clock, LogOut, Mail } from '@lucide/vue'

import LogoRivDinde from '../composants/LogoRivDinde.vue'
import { useAuthentification } from '../stores/authentification'

const session = useAuthentification()

const etapes = [
  { icone: CheckCircle2, titre: 'Inscription enregistree', texte: 'Vos informations nous sont parvenues.', fait: true },
  { icone: Clock, titre: 'Verification en cours', texte: 'Un administrateur controle votre dossier.', fait: false },
  { icone: Mail, titre: 'Activation', texte: 'Vous recevrez un courriel des que ce sera fait.', fait: false },
]
</script>

<template>
  <main class="flex min-h-screen w-full items-center justify-center px-6 py-12">
    <div class="carte-sombre w-full max-w-[520px] animate-[apparition_0.2s_ease-out] p-9">
      <div class="flex items-center gap-4">
        <LogoRivDinde :taille="52" />
        <div>
          <p class="text-[11px] tracking-wider text-marque uppercase">Compte en verification</p>
          <h1 class="mt-0.5 text-[21px] font-semibold tracking-tight text-white">
            Bonjour {{ session.utilisateur?.prenom }}
          </h1>
        </div>
      </div>

      <p class="mt-6 text-[14.5px] leading-relaxed text-[#b49a8c]">
        Votre espace s'ouvrira des qu'un administrateur aura verifie vos informations.
        C'est ce qui garantit a chaque client que les boutiques et les livreurs
        de la plateforme sont bien reels.
      </p>

      <!-- Une frise plutot qu'une phrase : on voit ou l'on en est, et ce qui
           reste. Le meme composant servira au suivi de commande. -->
      <ol class="mt-8 flex flex-col gap-0">
        <li v-for="(etape, index) in etapes" :key="etape.titre" class="flex gap-4">
          <div class="flex flex-col items-center">
            <span
              class="flex h-9 w-9 items-center justify-center rounded-full border transition-colors"
              :class="
                etape.fait
                  ? 'border-marque bg-marque/15 text-marque-clair'
                  : index === 1
                    ? 'border-amber-700 bg-amber-900/20 text-amber-300'
                    : 'border-[#4a2718] text-[#7c6459]'
              "
            >
              <component :is="etape.icone" :size="17" />
            </span>
            <span
              v-if="index < etapes.length - 1"
              class="my-1 w-px flex-1 bg-[#4a2718]"
              aria-hidden="true"
            />
          </div>
          <div class="pb-6">
            <b class="block text-[14.5px] font-semibold text-white">{{ etape.titre }}</b>
            <span class="text-[13px] text-[#b49a8c]">{{ etape.texte }}</span>
          </div>
        </li>
      </ol>

      <div class="flex flex-wrap items-center justify-between gap-3 border-t border-encre-3 pt-6">
        <RouterLink
          to="/"
          class="inline-flex items-center gap-2 text-[13px] text-[#b49a8c] transition-colors
                 duration-150 hover:text-marque-clair"
        >
          <ArrowLeft :size="15" />
          Parcourir le catalogue
        </RouterLink>
        <button type="button" class="bouton-discret" @click="session.deconnecter()">
          <LogOut :size="15" />
          Se deconnecter
        </button>
      </div>
    </div>
  </main>
</template>
