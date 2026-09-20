<script setup lang="ts">
// La fiche que le vendeur remplit : informations, photos, stock.
//
// Trois onglets plutot qu'un formulaire fleuve (regle d'or n°6) : on remplit
// les informations, puis on depose les photos, puis on ajuste le stock — et on
// ne voit jamais que ce qui concerne l'etape en cours.
import {
  ArrowLeft, Check, ImagePlus, Info, Layers, Package, Star, Trash2, TriangleAlert,
} from '@lucide/vue'
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { EchecApi } from '../../api/client'
import { vendeur, type Mouvement, type Photo } from '../../api/vendeur'

const route = useRoute()
const routeur = useRouter()

const identifiant = computed(() =>
  route.params.id ? Number(route.params.id) : null,
)
const creation = computed(() => identifiant.value === null)

const onglet = ref<'informations' | 'photos' | 'stock'>('informations')
const champs = ref({
  nom: '', description: '', prix_euros: '', poids_grammes: '',
  stock_disponible: '0', seuil_alerte: '5', est_visible: true,
})
const photos = ref<Photo[]>([])
const mouvements = ref<Mouvement[]>([])
const message = ref('')
const erreur = ref('')
const occupe = ref(false)

// Ajustement de stock
const ajustement = ref({ quantite: '', type: 'AJUSTEMENT', motif: '' })

async function charger() {
  if (creation.value) return
  const reponse = await vendeur.detail(identifiant.value as number)
  const donnees = reponse.data as never as {
    nom: string; description: string; prix_centimes: number; poids_grammes: number | null
    stock_disponible: number; photos: Photo[]
  }
  champs.value = {
    nom: donnees.nom,
    description: donnees.description ?? '',
    prix_euros: (donnees.prix_centimes / 100).toFixed(2),
    poids_grammes: String(donnees.poids_grammes ?? ''),
    stock_disponible: String(donnees.stock_disponible),
    seuil_alerte: '5',
    est_visible: true,
  }
  photos.value = donnees.photos ?? []
  mouvements.value = await vendeur.stock.mouvements(identifiant.value as number)
}

onMounted(charger)

function centimes(euros: string) {
  return Math.round(Number(String(euros).replace(',', '.')) * 100)
}

async function enregistrer() {
  erreur.value = ''
  message.value = ''
  occupe.value = true
  const donnees = {
    nom: champs.value.nom,
    description: champs.value.description,
    prix_unitaire_centimes: centimes(champs.value.prix_euros),
    poids_grammes: champs.value.poids_grammes ? Number(champs.value.poids_grammes) : null,
    seuil_alerte: Number(champs.value.seuil_alerte),
    est_visible: champs.value.est_visible,
  }
  try {
    if (creation.value) {
      const cree = (await vendeur.creer({
        ...donnees,
        stock_disponible: Number(champs.value.stock_disponible),
      })) as never as { id: number }
      // On enchaine sur les photos : un produit sans photo n'est pas
      // publiable, autant y emmener tout de suite.
      await routeur.replace({ name: 'vendeur-produit', params: { id: cree.id } })
      onglet.value = 'photos'
      message.value = 'Produit cree. Ajoutez maintenant ses photos.'
      await charger()
    } else {
      await vendeur.modifier(identifiant.value as number, donnees)
      message.value = 'Modifications enregistrees.'
    }
  } catch (echec) {
    erreur.value = echec instanceof EchecApi ? echec.erreur.message : 'Enregistrement impossible.'
  } finally {
    occupe.value = false
  }
}

async function deposerFichiers(evenement: Event | DragEvent) {
  erreur.value = ''
  const cible = evenement.target as HTMLInputElement
  const liste =
    'dataTransfer' in evenement && evenement.dataTransfer
      ? evenement.dataTransfer.files
      : cible.files
  if (!liste?.length || identifiant.value === null) return

  occupe.value = true
  try {
    photos.value = await vendeur.photos.ajouter(identifiant.value, Array.from(liste))
    message.value = 'Photos ajoutees.'
  } catch (echec) {
    erreur.value = echec instanceof Error ? echec.message : 'Televersement impossible.'
  } finally {
    occupe.value = false
  }
}

async function definirPrincipale(idPhoto: number) {
  const ordre = [idPhoto, ...photos.value.filter((p) => p.id !== idPhoto).map((p) => p.id)]
  photos.value = await vendeur.photos.ordonner(identifiant.value as number, ordre)
}

async function retirerPhoto(idPhoto: number) {
  photos.value = await vendeur.photos.retirer(identifiant.value as number, idPhoto)
}

async function appliquerAjustement() {
  erreur.value = ''
  occupe.value = true
  try {
    const resultat = await vendeur.stock.ajuster(
      identifiant.value as number,
      Number(ajustement.value.quantite),
      ajustement.value.type,
      ajustement.value.motif,
    )
    champs.value.stock_disponible = String(resultat.stock_disponible)
    mouvements.value = [resultat.mouvement, ...mouvements.value]
    ajustement.value = { quantite: '', type: 'AJUSTEMENT', motif: '' }
    message.value = 'Stock mis a jour.'
  } catch (echec) {
    erreur.value = echec instanceof EchecApi ? echec.erreur.message : 'Ajustement refuse.'
  } finally {
    occupe.value = false
  }
}

const ONGLETS = [
  { cle: 'informations', libelle: 'Informations', icone: Info },
  { cle: 'photos', libelle: 'Photos', icone: ImagePlus },
  { cle: 'stock', libelle: 'Stock', icone: Layers },
] as const
</script>

<template>
  <div class="mx-auto max-w-[840px] animate-[apparition_0.2s_ease-out]">
    <RouterLink
      :to="{ name: 'vendeur-catalogue' }"
      class="mb-5 inline-flex items-center gap-2 text-[13.5px] text-slate-500
             transition-colors hover:text-slate-900"
    >
      <ArrowLeft :size="15" />
      Retour au catalogue
    </RouterLink>

    <h2 class="text-[21px] font-semibold tracking-tight">
      {{ creation ? 'Nouveau produit' : champs.nom }}
    </h2>

    <!-- Onglets -->
    <div class="mt-5 flex gap-1 rounded-2xl bg-white p-1.5 ring-1 ring-slate-200">
      <button
        v-for="element in ONGLETS"
        :key="element.cle"
        type="button"
        class="flex flex-1 items-center justify-center gap-2 rounded-xl py-2.5 text-[13.5px]
               transition-colors duration-150 disabled:opacity-40"
        :class="onglet === element.cle ? 'text-white' : 'text-slate-600 hover:bg-slate-50'"
        :style="onglet === element.cle ? { background: 'var(--accent)' } : undefined"
        :disabled="creation && element.cle !== 'informations'"
        :title="creation && element.cle !== 'informations'
          ? 'Enregistrez d abord les informations'
          : undefined"
        @click="onglet = element.cle"
      >
        <component :is="element.icone" :size="16" />
        {{ element.libelle }}
      </button>
    </div>

    <p
      v-if="message"
      class="mt-4 flex items-center gap-2 rounded-xl bg-emerald-50 px-4 py-3 text-[13px]
             text-emerald-800"
    >
      <Check :size="15" /> {{ message }}
    </p>
    <p
      v-if="erreur"
      class="mt-4 flex items-center gap-2 rounded-xl bg-red-50 px-4 py-3 text-[13px] text-red-700"
    >
      <TriangleAlert :size="15" /> {{ erreur }}
    </p>

    <!-- ── Informations ──────────────────────────────────────────────── -->
    <form
      v-if="onglet === 'informations'"
      class="mt-4 rounded-2xl border border-slate-200 bg-white p-6"
      @submit.prevent="enregistrer"
    >
      <div class="flex flex-col gap-4">
        <label class="flex flex-col gap-1.5">
          <span class="text-[13px] font-medium text-slate-600">Nom du produit</span>
          <input v-model="champs.nom" required class="champ-clair" />
        </label>

        <label class="flex flex-col gap-1.5">
          <span class="text-[13px] font-medium text-slate-600">Description</span>
          <textarea v-model="champs.description" rows="3" class="champ-clair" />
        </label>

        <div class="flex flex-wrap gap-4">
          <label class="flex flex-1 flex-col gap-1.5">
            <span class="text-[13px] font-medium text-slate-600">Prix (euros)</span>
            <input v-model="champs.prix_euros" required inputmode="decimal" class="champ-clair" />
          </label>
          <label class="flex flex-1 flex-col gap-1.5">
            <span class="text-[13px] font-medium text-slate-600">Poids (grammes)</span>
            <input v-model="champs.poids_grammes" inputmode="numeric" class="champ-clair" />
          </label>
          <label v-if="creation" class="flex flex-1 flex-col gap-1.5">
            <span class="text-[13px] font-medium text-slate-600">Stock initial</span>
            <input v-model="champs.stock_disponible" inputmode="numeric" class="champ-clair" />
          </label>
          <label class="flex flex-1 flex-col gap-1.5">
            <span class="text-[13px] font-medium text-slate-600">Seuil d alerte</span>
            <input v-model="champs.seuil_alerte" inputmode="numeric" class="champ-clair" />
          </label>
        </div>
      </div>

      <button
        type="submit"
        class="mt-6 inline-flex items-center gap-2 rounded-xl px-5 py-2.5 text-[13.5px]
               font-semibold text-white disabled:opacity-60"
        :style="{ background: 'var(--accent)' }"
        :disabled="occupe"
      >
        <Check :size="16" />
        {{ creation ? 'Creer le produit' : 'Enregistrer' }}
      </button>
    </form>

    <!-- ── Photos ────────────────────────────────────────────────────── -->
    <section v-else-if="onglet === 'photos'" class="mt-4 rounded-2xl border border-slate-200
                                                    bg-white p-6">
      <div
        class="flex flex-col items-center rounded-2xl border-2 border-dashed border-slate-200
               px-6 py-10 text-center transition-colors hover:border-slate-300"
        @dragover.prevent
        @drop.prevent="deposerFichiers"
      >
        <ImagePlus :size="26" class="text-slate-400" />
        <b class="mt-3 text-[14px]">Glissez vos photos ici</b>
        <p class="mt-1 text-[12.5px] text-slate-500">
          Six au maximum · JPEG, PNG ou WebP · 5 Mo et 600 x 600 pixels minimum
        </p>
        <label
          class="mt-4 cursor-pointer rounded-xl border border-slate-200 px-4 py-2 text-[13px]
                 transition-colors hover:bg-slate-50"
        >
          Choisir des fichiers
          <input type="file" accept="image/*" multiple class="hidden" @change="deposerFichiers" />
        </label>
      </div>

      <div v-if="photos.length" class="mt-6 grid grid-cols-2 gap-4 sm:grid-cols-3">
        <figure
          v-for="(photo, index) in photos"
          :key="photo.id"
          class="group relative overflow-hidden rounded-xl border border-slate-200"
        >
          <img :src="photo.url" :alt="photo.texte_alternatif" class="aspect-4/3 w-full object-cover" />

          <figcaption
            v-if="index === 0"
            class="absolute top-2 left-2 flex items-center gap-1 rounded-full bg-white/90 px-2
                   py-0.5 text-[11px] font-semibold text-slate-700"
          >
            <Star :size="11" /> Principale
          </figcaption>

          <div class="absolute right-2 bottom-2 flex gap-1 opacity-0 transition-opacity
                      group-hover:opacity-100">
            <button
              v-if="index !== 0"
              type="button"
              class="flex h-8 w-8 items-center justify-center rounded-lg bg-white/95 text-slate-700
                     shadow hover:text-amber-600"
              title="Definir comme photo principale"
              @click="definirPrincipale(photo.id)"
            >
              <Star :size="15" />
            </button>
            <button
              type="button"
              class="flex h-8 w-8 items-center justify-center rounded-lg bg-white/95 text-slate-700
                     shadow hover:text-red-600"
              title="Supprimer cette photo"
              @click="retirerPhoto(photo.id)"
            >
              <Trash2 :size="15" />
            </button>
          </div>
        </figure>
      </div>

      <p v-else class="mt-6 text-center text-[13px] text-slate-500">
        Aucune photo pour l instant. Un produit sans photo n interesse personne.
      </p>
    </section>

    <!-- ── Stock ─────────────────────────────────────────────────────── -->
    <section v-else class="mt-4 flex flex-col gap-4">
      <div class="rounded-2xl border border-slate-200 bg-white p-6">
        <div class="flex items-center gap-3">
          <span
            class="flex h-11 w-11 items-center justify-center rounded-xl"
            :style="{ background: 'var(--accent-doux)', color: 'var(--accent)' }"
          >
            <Package :size="20" />
          </span>
          <div>
            <p class="text-[11px] tracking-wider text-slate-500 uppercase">Stock actuel</p>
            <b class="text-[22px]">{{ champs.stock_disponible }}</b>
          </div>
        </div>

        <form class="mt-6 flex flex-wrap items-end gap-3" @submit.prevent="appliquerAjustement">
          <label class="flex w-28 flex-col gap-1.5">
            <span class="text-[13px] font-medium text-slate-600">Quantite</span>
            <input
              v-model="ajustement.quantite"
              required
              placeholder="+5 ou -2"
              class="champ-clair"
            />
          </label>
          <label class="flex w-44 flex-col gap-1.5">
            <span class="text-[13px] font-medium text-slate-600">Type</span>
            <select v-model="ajustement.type" class="champ-clair">
              <option value="REAPPRO">Reapprovisionnement</option>
              <option value="AJUSTEMENT">Ajustement manuel</option>
              <option value="RETOUR">Retour</option>
            </select>
          </label>
          <label class="flex min-w-[200px] flex-1 flex-col gap-1.5">
            <span class="text-[13px] font-medium text-slate-600">
              Motif
              <span v-if="ajustement.type === 'AJUSTEMENT'" class="text-red-600">obligatoire</span>
            </span>
            <input
              v-model="ajustement.motif"
              :required="ajustement.type === 'AJUSTEMENT'"
              placeholder="Casse, inventaire, erreur de saisie…"
              class="champ-clair"
            />
          </label>
          <button
            type="submit"
            class="rounded-xl px-5 py-2.5 text-[13.5px] font-semibold text-white disabled:opacity-60"
            :style="{ background: 'var(--accent)' }"
            :disabled="occupe"
          >
            Appliquer
          </button>
        </form>

        <p class="mt-3 text-[12px] text-slate-500">
          Un ajustement manuel sans motif est refuse : c est ce qui permet de retrouver,
          le lendemain, pourquoi un chiffre a bouge.
        </p>
      </div>

      <div class="overflow-hidden rounded-2xl border border-slate-200 bg-white">
        <table class="w-full text-[13px]">
          <thead>
            <tr class="border-b border-slate-200 text-left text-[11px] tracking-wider
                       text-slate-500 uppercase">
              <th class="px-4 py-3 font-semibold">Date</th>
              <th class="px-4 py-3 font-semibold">Type</th>
              <th class="px-4 py-3 font-semibold">Quantite</th>
              <th class="px-4 py-3 font-semibold">Apres</th>
              <th class="px-4 py-3 font-semibold">Motif</th>
              <th class="px-4 py-3 font-semibold">Par</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="mouvement in mouvements" :key="mouvement.id"
                class="border-b border-slate-100 last:border-0">
              <td class="px-4 py-2.5 text-slate-500">
                {{ new Date(mouvement.date_mouvement).toLocaleString('fr-FR') }}
              </td>
              <td class="px-4 py-2.5">{{ mouvement.libelle_type }}</td>
              <td
                class="px-4 py-2.5 font-semibold"
                :class="mouvement.quantite > 0 ? 'text-emerald-700' : 'text-red-700'"
              >
                {{ mouvement.quantite > 0 ? '+' : '' }}{{ mouvement.quantite }}
              </td>
              <td class="px-4 py-2.5">{{ mouvement.stock_apres }}</td>
              <td class="px-4 py-2.5 text-slate-500">{{ mouvement.motif || '—' }}</td>
              <td class="px-4 py-2.5 text-slate-500">{{ mouvement.auteur }}</td>
            </tr>
            <tr v-if="!mouvements.length">
              <td colspan="6" class="px-4 py-8 text-center text-slate-500">
                Aucun mouvement pour l instant.
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </div>
</template>
