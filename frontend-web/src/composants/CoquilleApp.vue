<script setup lang="ts">
// LA coquille — la seule. Sidebar retractable a gauche, navbar en haut,
// panneau retractable a droite (regles d'or 6 et 8).
//
// Elle habille **aussi bien le catalogue public que les espaces de travail**.
// C'etait le reproche du bloc H-6 : les CMS decident de l'affichage du contenu
// et des animations, pas de la structure ni des couleurs. Un visiteur et un
// vendeur voient donc le meme cadre ; seul le contenu change.
import {
  Bell, ChevronsLeft, LogIn, LogOut, Search, ShoppingCart, Smartphone, UserRound,
} from '@lucide/vue'
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import BandeauLivrerA from './BandeauLivrerA.vue'
import LogoRivDinde from './LogoRivDinde.vue'
import PanneauLateral from './PanneauLateral.vue'
import { descriptionDuRole } from '../roles'
import { useAuthentification } from '../stores/authentification'
import { useCatalogue } from '../stores/catalogue'
import { usePanier } from '../stores/panier'

const session = useAuthentification()
const catalogue = useCatalogue()
const panier = usePanier()
const route = useRoute()
const routeur = useRouter()

const sidebarOuverte = ref(true)

const role = computed(() => descriptionDuRole(session.role))
const surLeCatalogue = computed(() => route.name === 'vitrine')

const initiales = computed(() => {
  const u = session.utilisateur
  return u ? `${u.prenom[0] ?? ''}${u.nom[0] ?? ''}`.toUpperCase() : ''
})

const entreeActive = computed(() =>
  role.value.navigation.findIndex((entree) => entree.route === route.name),
)
const titre = computed(
  () => role.value.navigation[entreeActive.value]?.libelle ?? role.value.espace,
)

// La barre de recherche pilote le catalogue. Depuis un autre ecran, chercher
// ramene sur le catalogue : c'est ce que fait toute plateforme marchande.
const recherche = ref(catalogue.recherche)
watch(recherche, (valeur) => {
  if (!surLeCatalogue.value) routeur.push({ name: 'vitrine' })
  catalogue.chercher(valeur)
})
watch(() => catalogue.recherche, (valeur) => {
  if (valeur !== recherche.value) recherche.value = valeur
})
</script>

<template>
  <div
    class="flex min-h-screen w-full bg-atelier text-slate-900"
    :style="{ '--accent': role.accent, '--accent-doux': role.accentDoux }"
  >
    <!-- ── Sidebar ──────────────────────────────────────────────────── -->
    <aside
      class="flex shrink-0 flex-col bg-ardoise text-slate-300 transition-[width] duration-200"
      :class="sidebarOuverte ? 'w-[248px]' : 'w-[76px]'"
    >
      <RouterLink :to="{ name: 'vitrine' }" class="flex h-[68px] items-center gap-3 px-5">
        <LogoRivDinde :taille="34" />
        <span v-if="sidebarOuverte" class="font-semibold tracking-tight text-white">RivDinde</span>
      </RouterLink>

      <nav class="flex flex-col gap-0.5 px-3">
        <component
          :is="entree.route ? 'RouterLink' : 'button'"
          v-for="(entree, index) in role.navigation"
          :key="entree.libelle"
          :to="entree.route ? { name: entree.route } : undefined"
          :type="entree.route ? undefined : 'button'"
          :title="entree.libelle"
          class="group relative flex items-center gap-3 rounded-xl px-3 py-2.5 text-left
                 text-[13.5px] transition-colors duration-150"
          :class="
            index === entreeActive
              ? 'text-white'
              : 'text-slate-400 hover:bg-white/6 hover:text-slate-100'
          "
          :style="index === entreeActive ? { background: 'var(--accent)' } : undefined"
        >
          <component :is="entree.icone" :size="18" class="shrink-0" />
          <span v-if="sidebarOuverte" class="truncate">{{ entree.libelle }}</span>
          <span
            v-if="sidebarOuverte && entree.prochainement"
            class="ml-auto rounded-full bg-white/10 px-1.5 py-0.5 text-[10px] text-slate-300"
          >
            bientot
          </span>
        </component>
      </nav>

      <!-- Les filtres du catalogue vivent dans la sidebar, pas dans la page :
           c'est la place que leur donnent les regles d'or, et celle que leur
           donnent les catalogues marchands. -->
      <div v-if="surLeCatalogue && sidebarOuverte" class="mt-6 flex flex-col gap-5 px-3 pb-4">
        <slot name="filtres" />
      </div>

      <button
        type="button"
        class="mt-auto mx-3 mb-3 flex items-center gap-2.5 rounded-xl px-3 py-2.5 text-[12.5px]
               text-slate-500 transition-colors duration-150 hover:bg-white/6 hover:text-slate-300"
        @click="sidebarOuverte = !sidebarOuverte"
      >
        <ChevronsLeft
          :size="17"
          class="transition-transform duration-200"
          :class="sidebarOuverte ? '' : 'rotate-180'"
        />
        <span v-if="sidebarOuverte">Replier le menu</span>
      </button>
    </aside>

    <!-- ── Colonne centrale ─────────────────────────────────────────── -->
    <div class="flex min-w-0 flex-1 flex-col">
      <header
        class="flex h-[68px] shrink-0 items-center justify-between gap-5 border-b
               border-slate-200 bg-white px-6"
      >
        <div class="min-w-0">
          <p class="text-[11px] font-bold tracking-[0.09em] uppercase"
             :style="{ color: role.accent }">
            {{ role.espace }}
          </p>
          <h1 class="truncate text-[17px] font-semibold tracking-tight">{{ titre }}</h1>
        </div>

        <div class="flex items-center gap-2.5">
          <BandeauLivrerA v-if="surLeCatalogue" clair class="hidden xl:block" />

          <div class="relative hidden md:block">
            <Search :size="16" class="absolute top-1/2 left-3 -translate-y-1/2 text-slate-400" />
            <input
              v-model="recherche"
              type="search"
              placeholder="Rechercher…"
              class="w-56 rounded-xl border border-slate-200 bg-slate-50 py-2 pr-3 pl-9
                     text-[13.5px] transition-colors duration-150 focus:border-slate-300
                     focus:bg-white focus:outline-none"
            />
          </div>

          <button
            type="button"
            class="relative flex h-9 w-9 items-center justify-center rounded-xl border
                   border-slate-200 text-slate-600 transition-colors duration-150
                   hover:bg-slate-50 lg:hidden"
            title="Mon panier"
            @click="panier.ouvert = !panier.ouvert"
          >
            <ShoppingCart :size="17" />
            <span
              v-if="panier.nombreArticles"
              class="absolute -top-1 -right-1 flex h-[17px] min-w-[17px] items-center
                     justify-center rounded-full px-1 text-[10px] font-bold text-white"
              :style="{ background: role.accent }"
            >
              {{ panier.nombreArticles }}
            </span>
          </button>

          <template v-if="session.estConnecte">
            <div class="ml-1 flex items-center gap-2.5 border-l border-slate-200 pl-3">
              <span
                class="flex h-9 w-9 items-center justify-center rounded-full text-[12.5px]
                       font-bold"
                :style="{ background: role.accentDoux, color: role.accent }"
              >
                {{ initiales }}
              </span>
              <div class="hidden leading-tight sm:block">
                <b class="block text-[13px]">{{ session.utilisateur?.prenom }}</b>
                <span class="text-[11.5px] text-slate-500">{{ session.utilisateur?.email }}</span>
              </div>
              <button
                type="button"
                title="Se deconnecter"
                class="flex h-9 w-9 items-center justify-center rounded-xl text-slate-500
                       transition-colors duration-150 hover:bg-red-50 hover:text-red-600"
                @click="session.deconnecter()"
              >
                <LogOut :size="17" />
              </button>
            </div>
          </template>

          <template v-else>
            <RouterLink
              :to="{ name: 'connexion' }"
              class="flex items-center gap-2 rounded-xl border border-slate-200 px-3 py-2
                     text-[13px] text-slate-700 transition-colors hover:bg-slate-50"
            >
              <LogIn :size="15" />
              <span class="hidden sm:block">Se connecter</span>
            </RouterLink>
            <RouterLink
              :to="{ name: 'inscription' }"
              class="hidden items-center gap-2 rounded-xl px-3.5 py-2 text-[13px] font-semibold
                     text-white transition-opacity hover:opacity-90 sm:flex"
              :style="{ background: role.accent }"
            >
              <UserRound :size="15" />
              Creer un compte
            </RouterLink>
          </template>
        </div>
      </header>

      <!-- Le livreur travaille sur son telephone : le lui dire vaut mieux que
           lui servir des ecrans web a moitie utiles (bloc H-9). -->
      <p
        v-if="role.plateforme === 'mobile'"
        class="flex items-center gap-2.5 border-b border-violet-200 bg-violet-50 px-6 py-2.5
               text-[13px] text-violet-900"
      >
        <Smartphone :size="16" />
        L espace livreur se utilise depuis l application mobile. Cet ecran web sert au
        suivi, pas aux courses.
      </p>

      <main class="flex-1 overflow-x-hidden p-6">
        <slot />
      </main>
    </div>

    <!-- ── Panneau lateral droit, stable et retractable ─────────────── -->
    <PanneauLateral />
  </div>
</template>
