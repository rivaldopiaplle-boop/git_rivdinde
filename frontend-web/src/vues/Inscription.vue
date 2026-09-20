<script setup lang="ts">
import { ArrowLeft, Bike, KeyRound, Mail, Store, User, UserPlus } from '@lucide/vue'
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { EchecApi } from '../api/client'
import { accueilDuRole } from '../routeur'
import ChampTexte from '../composants/ChampTexte.vue'
import LogoRivDinde from '../composants/LogoRivDinde.vue'
import PanneauMarque from '../composants/PanneauMarque.vue'
import { useAuthentification } from '../stores/authentification'

type Profil = 'client' | 'vendeur' | 'livreur'

const session = useAuthentification()
const routeur = useRouter()
const route = useRoute()

// La page « rejoindre » arrive ici avec ?profil=vendeur : le formulaire est
// deja sur le bon onglet, personne n'a a le rechercher.
const profilDemande = route.query.profil as Profil | undefined
const profil = ref<Profil>(
  profilDemande && ['client', 'vendeur', 'livreur'].includes(profilDemande)
    ? profilDemande
    : 'client',
)
const PROFILS: { cle: Profil; libelle: string; icone: typeof User }[] = [
  { cle: 'client', libelle: 'Client', icone: User },
  { cle: 'vendeur', libelle: 'Vendeur', icone: Store },
  { cle: 'livreur', libelle: 'Livreur', icone: Bike },
]

const champs = ref({
  prenom: '', nom: '', email: '', mot_de_passe: '',
  nom_boutique: '', type_activite: 'EXPRESS',
  mode_livraison: 'EXPRESS', vehicule: 'VELO',
})
const erreur = ref('')
const details = ref<Record<string, string[]>>({})

// Dit avant l'envoi, pas apres : un vendeur doit savoir qu'il sera verifie
// avant de pouvoir travailler (D-02).
const avertissement = computed(() =>
  profil.value === 'client'
    ? ''
    : 'Votre compte sera cree, puis verifie par un administrateur avant activation.',
)

async function valider() {
  erreur.value = ''
  details.value = {}
  const commun = {
    email: champs.value.email,
    mot_de_passe: champs.value.mot_de_passe,
    nom: champs.value.nom,
    prenom: champs.value.prenom,
  }
  const specifique =
    profil.value === 'vendeur'
      ? { nom_boutique: champs.value.nom_boutique, type_activite: champs.value.type_activite }
      : profil.value === 'livreur'
        ? { mode_livraison: champs.value.mode_livraison, vehicule: champs.value.vehicule }
        : {}

  try {
    await session.inscrire(profil.value, { ...commun, ...specifique })
    await routeur.push({
      name: session.enAttenteDeValidation ? 'en-attente' : accueilDuRole(session.role),
    })
  } catch (echec) {
    if (echec instanceof EchecApi) {
      erreur.value = echec.erreur.message
      details.value = echec.erreur.details
    } else {
      erreur.value = "L'inscription n'a pas abouti."
    }
  }
}
</script>

<template>
  <div class="flex min-h-screen w-full">
    <PanneauMarque />

    <main class="flex flex-1 items-center justify-center px-6 py-12">
      <form class="w-full max-w-[440px] animate-[apparition_0.2s_ease-out]" @submit.prevent="valider">
        <RouterLink
          to="/"
          class="mb-6 inline-flex items-center gap-2 text-[13px] text-[#b49a8c]
                 transition-colors duration-150 hover:text-marque-clair"
        >
          <ArrowLeft :size="15" />
          Retour au catalogue
        </RouterLink>

        <div class="mb-6 lg:hidden">
          <LogoRivDinde :taille="52" />
        </div>

        <h2 class="text-[26px] font-semibold tracking-tight text-white">Creer un compte</h2>
        <p class="mt-1 mb-6 text-[14px] text-[#b49a8c]">Choisissez d'abord votre role.</p>

        <!-- Onglets : le choix du role change le formulaire, il doit donc etre
             visible en premier et non cache dans une liste deroulante. -->
        <div class="mb-5 flex gap-1 rounded-2xl bg-[#23130d] p-1.5">
          <button
            v-for="choix in PROFILS"
            :key="choix.cle"
            type="button"
            class="flex flex-1 items-center justify-center gap-2 rounded-xl py-2.5 text-[13.5px]
                   transition-all duration-150"
            :class="
              profil === choix.cle
                ? 'bg-marque font-bold text-encre'
                : 'text-[#b49a8c] hover:bg-white/5'
            "
            @click="profil = choix.cle"
          >
            <component :is="choix.icone" :size="16" />
            {{ choix.libelle }}
          </button>
        </div>

        <p
          v-if="avertissement"
          class="mb-5 rounded-xl border border-amber-900/60 bg-amber-950/25 px-3.5 py-3
                 text-[13px] text-amber-200"
        >
          {{ avertissement }}
        </p>

        <div class="flex flex-col gap-4">
          <div class="flex gap-3">
            <ChampTexte v-model="champs.prenom" label="Prenom" :icone="User" requis class="flex-1" />
            <ChampTexte v-model="champs.nom" label="Nom" requis class="flex-1" />
          </div>

          <ChampTexte
            v-model="champs.email"
            label="Adresse e-mail"
            type="email"
            :icone="Mail"
            autocomplete="email"
            requis
            :erreur="details.email?.[0]"
          />
          <ChampTexte
            v-model="champs.mot_de_passe"
            label="Mot de passe"
            type="password"
            :icone="KeyRound"
            autocomplete="new-password"
            aide="Dix caracteres au minimum, et pas un mot de passe courant."
            requis
            :minlength="10"
            :erreur="details.mot_de_passe?.[0]"
          />

          <template v-if="profil === 'vendeur'">
            <ChampTexte
              v-model="champs.nom_boutique"
              label="Nom de la boutique"
              :icone="Store"
              requis
            />
            <label class="flex flex-col gap-1.5">
              <span class="text-[13px] font-medium text-[#c9b4a6]">Type d'activite</span>
              <select v-model="champs.type_activite" class="champ">
                <option value="EXPRESS">Express — restauration, livraison immediate</option>
                <option value="STANDARD">Standard — colis, passage par entrepot</option>
              </select>
            </label>
          </template>

          <template v-if="profil === 'livreur'">
            <label class="flex flex-col gap-1.5">
              <span class="text-[13px] font-medium text-[#c9b4a6]">Mode de livraison</span>
              <select v-model="champs.mode_livraison" class="champ">
                <option value="EXPRESS">Express — une course a la fois</option>
                <option value="STANDARD">Standard — tournees depuis un entrepot</option>
              </select>
            </label>
            <label class="flex flex-col gap-1.5">
              <span class="text-[13px] font-medium text-[#c9b4a6]">Vehicule</span>
              <select v-model="champs.vehicule" class="champ">
                <option value="VELO">Velo</option>
                <option value="SCOOTER">Scooter</option>
                <option value="VOITURE">Voiture</option>
                <option value="CAMIONNETTE">Camionnette</option>
              </select>
            </label>
          </template>
        </div>

        <p
          v-if="erreur"
          class="mt-4 rounded-xl border border-red-900/70 bg-red-950/40 px-3.5 py-3
                 text-[13px] text-red-200"
          role="alert"
        >
          {{ erreur }}
        </p>

        <button type="submit" class="bouton-marque mt-6 w-full" :disabled="session.chargement">
          <UserPlus :size="17" />
          {{ session.chargement ? 'Creation…' : 'Creer mon compte' }}
        </button>

        <p class="mt-5 text-center text-[13.5px] text-[#b49a8c]">
          Deja inscrit ?
          <RouterLink to="/connexion" class="text-marque-clair hover:underline">
            Se connecter
          </RouterLink>
        </p>
      </form>
    </main>
  </div>
</template>
