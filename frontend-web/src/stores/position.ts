// Ou le visiteur se fait livrer.
//
// Sans cette information, le catalogue Express ne peut pas s'afficher : une
// boutique Express hors du rayon n'apparait pas du tout (D-09). Plutot que de
// montrer un catalogue vide sans explication, on demande la ville des
// l'arrivee — c'est le comportement que les clients connaissent deja des
// plateformes de livraison (D-22).
import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

export type Ville = { nom: string; lat: number; lon: number }

// Au MVP, une liste de villes plutot qu'un champ libre : geocoder une saisie
// libre demande un appel a Nominatim a chaque frappe (D-25), pour un confort
// qui n'apporte rien tant que la demonstration se joue sur une seule ville.
export const VILLES: Ville[] = [
  { nom: 'Lyon', lat: 45.755, lon: 4.832 },
  { nom: 'Villeurbanne', lat: 45.7719, lon: 4.8902 },
  { nom: 'Paris', lat: 48.8566, lon: 2.3522 },
  { nom: 'Marseille', lat: 43.2965, lon: 5.3698 },
  { nom: 'Bordeaux', lat: 44.8378, lon: -0.5792 },
]

const CLE = 'rivdinde.position'

export const usePosition = defineStore('position', () => {
  const ville = ref<Ville | null>(null)
  const localisationEnCours = ref(false)

  const connue = computed(() => ville.value !== null)
  const libelle = computed(() => ville.value?.nom ?? 'Choisir une ville')

  function restaurer() {
    const brut = localStorage.getItem(CLE)
    if (brut) {
      try {
        ville.value = JSON.parse(brut)
      } catch {
        localStorage.removeItem(CLE)
      }
    }
  }

  function choisir(nouvelle: Ville) {
    ville.value = nouvelle
    localStorage.setItem(CLE, JSON.stringify(nouvelle))
  }

  function oublier() {
    ville.value = null
    localStorage.removeItem(CLE)
  }

  /** Propose la geolocalisation du navigateur, et retombe sur la ville la
   *  plus proche de la liste. Le refus est un cas normal, pas une erreur. */
  function localiser() {
    if (!navigator.geolocation) return
    localisationEnCours.value = true
    navigator.geolocation.getCurrentPosition(
      ({ coords }) => {
        const plusProche = VILLES.reduce((a, b) =>
          Math.hypot(a.lat - coords.latitude, a.lon - coords.longitude) <
          Math.hypot(b.lat - coords.latitude, b.lon - coords.longitude)
            ? a
            : b,
        )
        choisir(plusProche)
        localisationEnCours.value = false
      },
      () => {
        localisationEnCours.value = false
      },
      { timeout: 8000 },
    )
  }

  /** Les parametres a joindre a un appel catalogue. */
  const parametres = computed(() =>
    ville.value ? `lat=${ville.value.lat}&lon=${ville.value.lon}` : '',
  )

  return { ville, connue, libelle, parametres, localisationEnCours, restaurer, choisir, oublier, localiser }
})
