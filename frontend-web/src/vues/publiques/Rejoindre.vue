<script setup lang="ts">
// La page qu'un futur vendeur ou un futur livreur ouvre avant de decider.
//
// Elle existe parce que l'inscription seule ne suffit pas : personne ne cree
// un compte professionnel sans savoir ce qu'il y gagne, ce qu'on lui demande,
// et combien de temps la verification prend.
import { ArrowRight, Bike, CheckCircle2, Store } from '@lucide/vue'

const offres = [
  {
    cle: 'vendeur',
    icone: Store,
    titre: 'Vendre sur RivDinde',
    accroche: 'Restaurant, boutique, artisan : votre catalogue en ligne en une apres-midi.',
    points: [
      'Choisissez votre rythme : Express pour la livraison immediate, Standard pour le colis',
      'Vos photos, vos prix, votre stock — vous gardez la main sur tout',
      'Un compte pour votre personnel, sans lui donner acces a votre chiffre d affaires',
      'Paiement reverse automatiquement, commission connue d avance',
    ],
    demande: 'Un nom de boutique, une adresse, et un numero SIRET.',
  },
  {
    cle: 'livreur',
    icone: Bike,
    titre: 'Livrer avec RivDinde',
    accroche: 'A velo, en scooter ou en camionnette, a votre rythme.',
    points: [
      'Express : une course a la fois, autour de vous, acceptee ou refusee librement',
      'Standard : des tournees preparees, groupees, depuis un entrepot',
      'La remuneration de chaque course est affichee avant que vous l acceptiez',
      'Vous choisissez quand vous etes disponible',
    ],
    demande: 'Une piece d identite et un vehicule.',
  },
]
</script>

<template>
  <div class="mx-auto max-w-[1240px] px-5 py-14">
    <p class="text-[12px] tracking-[0.16em] text-marque uppercase">Rejoindre la plateforme</p>
    <h1 class="mt-3 max-w-[20ch] text-4xl leading-tight font-semibold tracking-tight text-white">
      Vendre ou livrer, en gardant la main.
    </h1>
    <p class="mt-4 max-w-[62ch] text-[15px] leading-relaxed text-[#b49a8c]">
      Les deux inscriptions sont gratuites et prennent deux minutes. Votre compte est
      ensuite verifie par un administrateur avant d etre active — c est ce qui garantit
      a chaque client que les boutiques et les livreurs sont bien reels.
    </p>

    <div class="mt-10 grid gap-6 lg:grid-cols-2">
      <article
        v-for="offre in offres"
        :key="offre.cle"
        class="flex flex-col rounded-2xl border border-encre-3 bg-encre-2/40 p-7 transition-colors
               duration-200 hover:border-marque/40"
      >
        <span class="flex h-12 w-12 items-center justify-center rounded-2xl bg-marque/12 text-marque">
          <component :is="offre.icone" :size="22" />
        </span>

        <h2 class="mt-5 text-[21px] font-semibold tracking-tight text-white">{{ offre.titre }}</h2>
        <p class="mt-2 text-[14px] text-[#b49a8c]">{{ offre.accroche }}</p>

        <ul class="mt-6 flex flex-1 flex-col gap-3">
          <li v-for="point in offre.points" :key="point" class="flex gap-3">
            <CheckCircle2 :size="17" class="mt-0.5 shrink-0 text-marque/70" />
            <span class="text-[13.5px] leading-relaxed text-[#c9b4a6]">{{ point }}</span>
          </li>
        </ul>

        <p class="mt-6 rounded-xl bg-encre/60 px-4 py-3 text-[12.5px] text-[#b49a8c]">
          <b class="text-white">Ce qu on vous demande :</b> {{ offre.demande }}
        </p>

        <RouterLink
          :to="{ name: 'inscription', query: { profil: offre.cle } }"
          class="bouton-marque mt-5 w-full"
        >
          {{ offre.cle === 'vendeur' ? 'Ouvrir ma boutique' : 'Devenir livreur' }}
          <ArrowRight :size="17" />
        </RouterLink>
      </article>
    </div>

    <p class="mt-10 text-center text-[13.5px] text-[#b49a8c]">
      Vous cherchez plutot a commander ?
      <RouterLink to="/" class="text-marque-clair hover:underline">Voir le catalogue</RouterLink>
    </p>
  </div>
</template>
