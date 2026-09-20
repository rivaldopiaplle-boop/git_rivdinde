import { createPinia } from 'pinia'
import { createApp } from 'vue'

import App from './App.vue'
import { routeur } from './routeur'
import { useAuthentification } from './stores/authentification'
import { usePanier } from './stores/panier'
import { usePosition } from './stores/position'
import './style.css'

const application = createApp(App)
application.use(createPinia())

// PrimeVue est installe (D-26) mais volontairement PAS encore enregistre :
// son theme pese ~200 Ko, et aucun ecran de la tranche 1 n'utilise encore un
// de ses composants. Embarquer 200 Ko pour rien serait exactement le genre de
// detail qu'on reproche aux autres.
//
// Il sera branche ici a la tranche 2, au premier tableau triable a
// boutons-icones — c'est la qu'il fait gagner des semaines :
//
//   application.use(PrimeVue, { theme: { preset: Aura } })
//   application.use(ToastService)

// On restaure la session AVANT de brancher le routeur : sinon le garde
// s'execute sur un etat vide et renvoie un utilisateur deja connecte vers
// l'ecran de connexion, le temps d'un clignotement.
// Une erreur de rendu non rattrapee laisse l'application muette : les clics
// ne font plus rien et rien ne l'explique. On la rend au moins visible dans
// la console, avec le nom du composant fautif.
application.config.errorHandler = (erreur, _instance, information) => {
  console.error('[RivDinde] erreur de rendu —', information, erreur)
}

usePosition().restaurer()
usePanier().demarrer()

const session = useAuthentification()
session.restaurer().finally(() => {
  application.use(routeur)
  application.mount('#app')
})
