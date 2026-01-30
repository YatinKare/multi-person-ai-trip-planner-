<script lang="ts">
  import { onMount, setContext } from "svelte"
  import { writable } from "svelte/store"
  import CreateTripModal from "$lib/components/CreateTripModal.svelte"
  import type { PageData } from "./$types"

  interface Props {
    data: PageData
  }

  let { data }: Props = $props()

  const adminSectionStore = writable("trips")
  setContext("adminSection", adminSectionStore)

  let searchQuery = $state("")
  let selectedFilter = $state("all")

  // Filter trips based on search query and status filter
  const filteredTrips = $derived.by(() => {
    let result = data.trips || []

    // Apply search filter
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase()
      result = result.filter(trip =>
        trip.name.toLowerCase().includes(query) ||
        (trip.rough_timeframe && trip.rough_timeframe.toLowerCase().includes(query))
      )
    }

    // Apply status filter
    if (selectedFilter !== "all") {
      result = result.filter(trip => trip.status === selectedFilter)
    }

    return result
  })

  // Get badge class based on trip status
  function getStatusBadgeClass(status: string): string {
    const badges: Record<string, string> = {
      collecting: "badge-info",
      recommending: "badge-warning",
      voting: "badge-warning",
      planning: "badge-warning",
      finalized: "badge-success"
    }
    return badges[status] || "badge-neutral"
  }

  // Get status display text
  function getStatusText(status: string): string {
    const texts: Record<string, string> = {
      collecting: "Preferences",
      recommending: "AI Thinking",
      voting: "Voting",
      planning: "Planning",
      finalized: "Finalized"
    }
    return texts[status] || status
  }

  // Format relative time
  function getRelativeTime(dateString: string): string {
    const date = new Date(dateString)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMins / 60)
    const diffDays = Math.floor(diffHours / 24)
    const diffWeeks = Math.floor(diffDays / 7)
    const diffMonths = Math.floor(diffDays / 30)

    if (diffMins < 1) return "just now"
    if (diffMins < 60) return `${diffMins}m ago`
    if (diffHours < 24) return `${diffHours}h ago`
    if (diffDays < 7) return `${diffDays}d ago`
    if (diffWeeks < 4) return `${diffWeeks}w ago`
    return `${diffMonths}mo ago`
  }

  // Show create trip modal
  let showCreateModal = $state(false)
</script>

<svelte:head>
  <title>My Trips - TripSync</title>
</svelte:head>

<div class="max-w-7xl mx-auto">
  <!-- Page Heading -->
  <div class="mb-8 flex flex-col justify-between gap-4 md:flex-row md:items-center">
    <div>
      <h2 class="text-3xl font-extrabold tracking-tight md:text-4xl">My Trips</h2>
      <p class="mt-1 text-base-content/60">Manage your group adventures and itineraries.</p>
    </div>
    <button class="btn btn-primary gap-2" onclick={() => showCreateModal = true}>
      <span class="material-symbols-outlined text-xl">add</span>
      Create New Trip
    </button>
  </div>

  {#if data.trips.length === 0}
    <!-- Empty State -->
    <div class="flex flex-col items-center justify-center min-h-[60vh] text-center px-4">
      <div class="max-w-md">
        <div class="mb-6">
          <span class="material-symbols-outlined text-9xl text-base-content/20">flight_takeoff</span>
        </div>
        <h3 class="text-2xl font-bold mb-3">No trips yet?</h3>
        <p class="text-base-content/60 mb-6">
          Adventure is just a click away. Start planning your next group getaway in seconds.
        </p>
        <button class="btn btn-primary btn-lg gap-2" onclick={() => showCreateModal = true}>
          <span class="material-symbols-outlined text-xl">add_circle</span>
          <span>Create Your First Trip</span>
        </button>

        <!-- Feature Section -->
        <div class="mt-12 pt-8 border-t border-base-300">
          <h4 class="text-lg font-bold mb-6">How TripSync Works</h4>
          <div class="grid grid-cols-1 gap-4">
            <div class="card bg-base-200 border border-base-300">
              <div class="card-body items-center text-center gap-3 p-4">
                <div class="w-10 h-10 rounded-lg bg-base-300/50 flex items-center justify-center text-primary">
                  <span class="material-symbols-outlined text-xl">auto_awesome</span>
                </div>
                <div>
                  <h5 class="font-bold text-sm">1. Create</h5>
                  <p class="text-xs text-base-content/60">Let AI build your perfect itinerary</p>
                </div>
              </div>
            </div>
            <div class="card bg-base-200 border border-base-300">
              <div class="card-body items-center text-center gap-3 p-4">
                <div class="w-10 h-10 rounded-lg bg-base-300/50 flex items-center justify-center text-primary">
                  <span class="material-symbols-outlined text-xl">group_add</span>
                </div>
                <div>
                  <h5 class="font-bold text-sm">2. Invite</h5>
                  <p class="text-xs text-base-content/60">Sync up with friends instantly</p>
                </div>
              </div>
            </div>
            <div class="card bg-base-200 border border-base-300">
              <div class="card-body items-center text-center gap-3 p-4">
                <div class="w-10 h-10 rounded-lg bg-base-300/50 flex items-center justify-center text-primary">
                  <span class="material-symbols-outlined text-xl">flight_takeoff</span>
                </div>
                <div>
                  <h5 class="font-bold text-sm">3. Go!</h5>
                  <p class="text-xs text-base-content/60">Enjoy stress-free travel</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  {:else}
    <!-- Filters and Search -->
    <div class="mb-8 flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
      <!-- Search Bar -->
      <div class="w-full max-w-md">
        <label class="input input-bordered flex items-center gap-2 bg-base-200">
          <span class="material-symbols-outlined text-base-content/60">search</span>
          <input
            type="text"
            class="grow"
            placeholder="Search trips by name or location..."
            bind:value={searchQuery}
          />
        </label>
      </div>

      <!-- Filter Chips -->
      <div class="flex flex-wrap gap-2">
        <button
          class="btn btn-sm {selectedFilter === 'all' ? 'btn-neutral' : 'btn-ghost bg-base-300'}"
          onclick={() => selectedFilter = 'all'}
        >
          All Trips
        </button>
        <button
          class="btn btn-sm {selectedFilter === 'collecting' ? 'btn-neutral' : 'btn-ghost bg-base-300'}"
          onclick={() => selectedFilter = 'collecting'}
        >
          Collecting Preferences
        </button>
        <button
          class="btn btn-sm {selectedFilter === 'voting' ? 'btn-neutral' : 'btn-ghost bg-base-300'}"
          onclick={() => selectedFilter = 'voting'}
        >
          Voting
        </button>
        <button
          class="btn btn-sm {selectedFilter === 'planning' ? 'btn-neutral' : 'btn-ghost bg-base-300'}"
          onclick={() => selectedFilter = 'planning'}
        >
          Planning
        </button>
        <button
          class="btn btn-sm {selectedFilter === 'finalized' ? 'btn-neutral' : 'btn-ghost bg-base-300'}"
          onclick={() => selectedFilter = 'finalized'}
        >
          Finalized
        </button>
      </div>
    </div>

    <!-- Trips Grid -->
    <div class="grid grid-cols-1 gap-6 md:grid-cols-2 xl:grid-cols-3">
      {#each filteredTrips as trip (trip.id)}
        <div class="card bg-base-200 border border-base-300 shadow-md hover:shadow-xl hover:-translate-y-1 transition-all overflow-hidden group">
          <figure class="relative aspect-video">
            <div class="badge {getStatusBadgeClass(trip.status)} absolute left-3 top-3 z-10">
              {getStatusText(trip.status)}
            </div>
            <button class="btn btn-circle btn-ghost btn-sm absolute right-3 top-3 z-10 bg-black/40 backdrop-blur-md">
              <span class="material-symbols-outlined text-lg">more_horiz</span>
            </button>
            <!-- Placeholder gradient for trip image -->
            <div class="flex h-full w-full items-center justify-center bg-gradient-to-br from-base-300 to-base-100">
              <span class="material-symbols-outlined text-6xl text-white/20">
                {trip.status === 'finalized' ? 'check_circle' : 'map'}
              </span>
            </div>
          </figure>
          <div class="card-body p-5">
            <div class="flex items-start justify-between mb-3">
              <h3 class="card-title text-xl">{trip.name}</h3>
              {#if trip.status === 'recommending' || trip.status === 'planning'}
                <div class="flex items-center gap-1 text-xs font-medium text-primary">
                  <span class="material-symbols-outlined text-sm">auto_awesome</span>
                  <span>AI</span>
                </div>
              {/if}
            </div>
            <p class="text-sm text-base-content/60 mb-4">
              Updated {getRelativeTime(trip.updated_at)}
            </p>
            <div class="flex items-center justify-between border-t border-base-300 pt-4">
              <div class="text-sm text-base-content/60">
                <span class="material-symbols-outlined text-base align-middle">group</span>
                {trip.member_count} {trip.member_count === 1 ? 'member' : 'members'}
              </div>
              <a href="/trips/{trip.id}" class="btn btn-ghost btn-circle btn-sm">
                <span class="material-symbols-outlined">arrow_forward</span>
              </a>
            </div>
          </div>
        </div>
      {/each}

      <!-- Create New Card -->
      <button
        class="card bg-transparent border-2 border-dashed border-base-300 hover:border-primary hover:bg-base-200/50 transition-all min-h-[300px] flex items-center justify-center group"
        onclick={() => showCreateModal = true}
      >
        <div class="card-body items-center justify-center text-center">
          <div class="w-16 h-16 rounded-full bg-base-300 flex items-center justify-center group-hover:bg-primary/20 group-hover:text-primary transition-colors">
            <span class="material-symbols-outlined text-3xl">add</span>
          </div>
          <h3 class="card-title text-lg mt-4 group-hover:text-primary">Plan a New Trip</h3>
          <p class="text-sm text-base-content/60">Start from scratch or use AI</p>
        </div>
      </button>
    </div>

    {#if filteredTrips.length === 0}
      <div class="text-center py-12">
        <span class="material-symbols-outlined text-6xl text-base-content/20">search_off</span>
        <p class="mt-4 text-base-content/60">No trips found matching your filters.</p>
        <button class="btn btn-ghost btn-sm mt-2" onclick={() => { searchQuery = ''; selectedFilter = 'all' }}>
          Clear filters
        </button>
      </div>
    {/if}
  {/if}
</div>

<!-- Create Trip Modal -->
<CreateTripModal bind:open={showCreateModal} />

<style>
  /* Import Material Symbols font */
  @import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200');

  .material-symbols-outlined {
    font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
  }
</style>
