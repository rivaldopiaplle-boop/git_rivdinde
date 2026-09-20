<script setup lang="ts">
// Le champ de formulaire de toute l'application : libelle, icone, message
// d'erreur, aide. L'ecrire une fois evite que le troisieme ecran ait des
// champs legerement differents des deux premiers.
import type { Component } from 'vue'

defineProps<{
  label: string
  icone?: Component
  type?: string
  aide?: string
  erreur?: string
  autocomplete?: string
  requis?: boolean
  minlength?: number
}>()

const valeur = defineModel<string>({ required: true })
</script>

<template>
  <label class="flex flex-col gap-1.5">
    <span class="text-[13px] font-medium text-[#c9b4a6]">{{ label }}</span>

    <span class="relative flex items-center">
      <component
        :is="icone"
        v-if="icone"
        :size="17"
        class="pointer-events-none absolute left-3.5 text-[#8a6d5c]"
      />
      <input
        v-model="valeur"
        :type="type ?? 'text'"
        :required="requis"
        :minlength="minlength"
        :autocomplete="autocomplete"
        class="champ"
        :class="[icone ? 'pl-10' : '', erreur ? 'champ-erreur' : '']"
      />
    </span>

    <span v-if="erreur" class="text-[12px] text-red-300">{{ erreur }}</span>
    <span v-else-if="aide" class="text-[11.5px] text-[#8a6d5c]">{{ aide }}</span>
  </label>
</template>
