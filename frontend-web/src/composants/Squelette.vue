<script setup lang="ts">
// Un squelette plutot qu'une roue qui tourne : le contenu semble arriver deux
// fois plus vite a duree reelle identique (design-system.md § 9).
defineProps<{ largeur?: string; hauteur?: string; rond?: boolean }>()
</script>

<template>
  <span
    class="inline-block animate-pulse bg-current opacity-10"
    :class="rond ? 'rounded-full' : 'rounded-md'"
    :style="{ width: largeur ?? '100%', height: hauteur ?? '1rem' }"
  />
</template>
