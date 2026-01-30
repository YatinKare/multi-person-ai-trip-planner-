<script lang="ts">
  import { setContext } from "svelte"
  import { writable } from "svelte/store"
  import type { PageData } from "./$types"

  interface Props {
    data: PageData
  }

  let { data }: Props = $props()

  const adminSectionStore = writable("trips")
  setContext("adminSection", adminSectionStore)
</script>

<svelte:head>
  <title>Recommendations - {data.trip.name} - TripSync</title>
</svelte:head>

<div class="max-w-7xl mx-auto">
  <!-- Breadcrumbs -->
  <nav class="mb-4 flex items-center text-sm font-medium">
    <a class="text-base-content/60 hover:text-primary transition-colors" href="/trips">All Trips</a>
    <span class="mx-2 text-base-content/40">/</span>
    <a class="text-base-content/60 hover:text-primary transition-colors" href="/trips/{data.trip.id}">{data.trip.name}</a>
    <span class="mx-2 text-base-content/40">/</span>
    <span class="text-base-content font-bold">Recommendations</span>
  </nav>

  <!-- Header -->
  <div class="flex flex-col gap-4 mb-8">
    <h1 class="text-4xl md:text-5xl font-black text-white tracking-tight">
      Destination Recommendations
    </h1>
    <p class="text-base-content/60 text-lg">
      Vote on your favorite destinations. The organizer will select the final choice.
    </p>
  </div>

  <!-- Placeholder Content -->
  <div class="card bg-base-200 border border-base-300">
    <div class="card-body items-center text-center py-16">
      <span class="material-symbols-outlined text-6xl text-primary mb-4">travel_explore</span>
      <h2 class="text-2xl font-bold text-white mb-2">Recommendations Coming Soon</h2>
      <p class="text-base-content/60 max-w-md">
        The destination voting interface will be implemented in Phase 7.
        For now, this page serves as a placeholder for the AI-generated destination recommendations.
      </p>
      <a href="/trips/{data.trip.id}" class="btn btn-primary mt-6">
        <span class="material-symbols-outlined">arrow_back</span>
        Back to Dashboard
      </a>
    </div>
  </div>
</div>

<style>
  @import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200');

  .material-symbols-outlined {
    font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
  }
</style>
