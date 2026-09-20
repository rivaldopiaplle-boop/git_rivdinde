<script setup lang="ts">
import { ArrowLeft, KeyRound, LogIn, Mail, ShieldCheck } from '@lucide/vue'
import { ref } from 'vue'
import { useRouter } from 'vue-router'

import { EchecApi } from '../api/client'
import { accueilDuRole } from '../routeur'
import ChampTexte from '../composants/ChampTexte.vue'
import LogoRivDinde from '../composants/LogoRivDinde.vue'
import PanneauMarque from '../composants/PanneauMarque.vue'
import { useAuthentification } from '../stores/authentification'

const session = useAuthentification()
const routeur = useRouter()

const email = ref('')
const motDePasse = ref('')
const erreur = ref('')

// Les comptes de demonstration, cliquables : changer de role prend deux clics.
// C'est ce qui rend une demonstration a cinq roles tenable en dix minutes.
const COMPTES = [
  { email: 'lea@exemple.fr', qui: 'Cliente', accent: 'text-emerald-300 border-emerald-800/60' },
  { email: 'karim@exemple.fr', qui: 'Vendeur', accent: 'text-blue-300 border-blue-800/60' },
  { email: 'ines@exemple.fr', qui: 'En attente', accent: 'text-amber-300 border-amber-800/60' },
  { email: 'nadia@exemple.fr', qui: 'Gestion', accent: 'text-teal-300 border-teal-800/60' },
  { email: 'amine@exemple.fr', qui: 'Livreur', accent: 'text-violet-300 border-violet-800/60' },
  { email: 'admin@rivdinde.local', qui: 'Admin', accent: 'text-red-300 border-red-800/60' },
]

function remplir(compte: (typeof COMPTES)[number]) {
  email.value = compte.email
  motDePasse.value = 'Demonstration!2026'
  erreur.value = ''
}

async function valider() {
  erreur.value = ''
  try {
    await session.connecter(email.value, motDePasse.value)
    // Un client retourne au catalogue, ou il commande ; les autres roles
    // entrent dans leur espace de travail.
    await routeur.push({
      name: session.enAttenteDeValidation ? 'en-attente' : accueilDuRole(session.role),
    })
  } catch (echec) {
    erreur.value = echec instanceof EchecApi ? echec.erreur.message : 'Connexion impossible.'
  }
}
</script>

<template>
  <div class="flex min-h-screen w-full">
    <PanneauMarque />

    <main class="flex flex-1 items-center justify-center px-6 py-12">
      <form class="w-full max-w-[380px] animate-[apparition_0.2s_ease-out]" @submit.prevent="valider">
        <RouterLink
          to="/"
          class="mb-6 inline-flex items-center gap-2 text-[13px] text-[#b49a8c]
                 transition-colors duration-150 hover:text-marque-clair"
        >
          <ArrowLeft :size="15" />
          Retour au catalogue
        </RouterLink>

        <div class="mb-8 lg:hidden">
          <LogoRivDinde variante="complet" :taille="76" />
        </div>

        <h2 class="text-[26px] font-semibold tracking-tight text-white">Connexion</h2>
        <p class="mt-1 mb-7 text-[14px] text-[#b49a8c]">
          Entrez vos identifiants pour retrouver votre espace.
        </p>

        <div class="flex flex-col gap-4">
          <ChampTexte
            v-model="email"
            label="Adresse e-mail"
            type="email"
            :icone="Mail"
            autocomplete="email"
            requis
          />
          <ChampTexte
            v-model="motDePasse"
            label="Mot de passe"
            type="password"
            :icone="KeyRound"
            autocomplete="current-password"
            requis
          />
        </div>

        <p
          v-if="erreur"
          class="mt-4 flex items-start gap-2 rounded-xl border border-red-900/70 bg-red-950/40
                 px-3.5 py-3 text-[13px] text-red-200"
          role="alert"
        >
          <ShieldCheck :size="16" class="mt-0.5 shrink-0" />
          {{ erreur }}
        </p>

        <button type="submit" class="bouton-marque mt-6 w-full" :disabled="session.chargement">
          <LogIn :size="17" />
          {{ session.chargement ? 'Connexion…' : 'Se connecter' }}
        </button>

        <p class="mt-5 text-center text-[13.5px] text-[#b49a8c]">
          Pas encore de compte ?
          <RouterLink to="/inscription" class="text-marque-clair hover:underline">
            En creer un
          </RouterLink>
        </p>

        <div class="mt-8 border-t border-encre-3 pt-6">
          <p class="mb-3 text-center text-[11px] tracking-wider text-[#7c6459] uppercase">
            Comptes de demonstration
          </p>
          <div class="flex flex-wrap justify-center gap-2">
            <button
              v-for="compte in COMPTES"
              :key="compte.email"
              type="button"
              class="rounded-full border px-3 py-1.5 text-[11.5px] transition-colors
                     duration-150 hover:bg-white/5"
              :class="compte.accent"
              @click="remplir(compte)"
            >
              {{ compte.qui }}
            </button>
          </div>
        </div>
      </form>
    </main>
  </div>
</template>
