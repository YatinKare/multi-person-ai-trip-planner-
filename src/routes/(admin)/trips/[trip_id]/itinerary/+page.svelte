<script lang="ts">
  import type { PageData, ActionData } from "./$types"
  import type { Activity, DayItinerary } from "$lib/types"
  import ActivityCard from "$lib/components/ActivityCard.svelte"
  import { enhance } from "$app/forms"

  interface Props {
    data: PageData
    form: ActionData
  }

  let { data, form }: Props = $props()

  // Parse days from JSONB
  const days: DayItinerary[] =
    (data.itinerary?.days as unknown as DayItinerary[]) || []

  // Calculate trip length from days array
  const tripLengthDays = days.length

  // Get summary if it exists (might be in the itinerary object)
  const summary = (data.itinerary as any)?.summary || null

  // Group activities by time slot for each day
  function getActivitiesByTimeSlot(day: DayItinerary) {
    const morning = day.activities.filter((a) => a.time_slot === "morning")
    const afternoon = day.activities.filter((a) => a.time_slot === "afternoon")
    const evening = day.activities.filter((a) => a.time_slot === "evening")
    return { morning, afternoon, evening }
  }

  // Format cost
  function formatCost(cost: number): string {
    return `$${cost.toLocaleString()}`
  }

  // Get time slot icon
  function getTimeSlotIcon(timeSlot: string): string {
    const icons: Record<string, string> = {
      morning: "wb_sunny",
      afternoon: "light_mode",
      evening: "nightlight",
    }
    return icons[timeSlot] || "schedule"
  }

  // Get time slot label
  function getTimeSlotLabel(timeSlot: string): string {
    const labels: Record<string, string> = {
      morning: "Morning",
      afternoon: "Afternoon",
      evening: "Evening",
    }
    return labels[timeSlot] || timeSlot
  }

  // Check if user is organizer
  const isOrganizer = data.userRole === "organizer"
  const isFinalized = data.trip.status === "finalized"

  // Finalization modal state
  let showFinalizeModal = $state(false)
  let isSubmitting = $state(false)

  function openFinalizeModal() {
    showFinalizeModal = true
  }

  function closeFinalizeModal() {
    showFinalizeModal = false
  }
</script>

<svelte:head>
  <title>Itinerary - {data.trip.name} - TripSync</title>
</svelte:head>

<div class="max-w-7xl mx-auto py-6 px-4 md:px-8 lg:px-16">
  <!-- Breadcrumbs -->
  <nav class="mb-4 flex items-center text-sm font-medium">
    <a
      class="text-base-content/60 hover:text-primary transition-colors"
      href="/trips">All Trips</a
    >
    <span class="mx-2 text-base-content/40">/</span>
    <a
      class="text-base-content/60 hover:text-primary transition-colors"
      href="/trips/{data.trip.id}">{data.trip.name}</a
    >
    <span class="mx-2 text-base-content/40">/</span>
    <span class="text-base-content font-bold">Itinerary</span>
  </nav>

  <!-- Header -->
  <div class="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-8">
    <div class="flex flex-col gap-2">
      <h1 class="text-4xl md:text-5xl font-black text-white tracking-tight">
        {data.itinerary.destination_name}
      </h1>
      <div class="flex items-center gap-3 mt-1">
        <span class="badge badge-primary gap-2 p-3 font-bold">
          <span class="material-symbols-outlined text-sm">route</span>
          {tripLengthDays}
          {tripLengthDays === 1 ? "Day" : "Days"}
        </span>
        <span class="badge badge-neutral gap-2 p-3 font-bold">
          <span class="material-symbols-outlined text-sm">payments</span>
          {formatCost(data.itinerary.total_cost || 0)} per person
        </span>
        {#if isFinalized}
          <span class="badge badge-success gap-2 p-3 font-bold">
            <span class="material-symbols-outlined text-sm">check_circle</span>
            Finalized
          </span>
        {/if}
      </div>
    </div>
    <div class="flex flex-wrap gap-3">
      <a
        href="/trips/{data.trip.id}"
        class="btn btn-neutral flex items-center gap-2 font-bold"
      >
        <span class="material-symbols-outlined">arrow_back</span>
        Back to Dashboard
      </a>
      {#if isOrganizer && !isFinalized}
        <button
          class="btn btn-success flex items-center gap-2 font-bold"
          onclick={openFinalizeModal}
        >
          <span class="material-symbols-outlined">check_circle</span>
          Finalize Itinerary
        </button>
      {/if}
    </div>
  </div>

  <!-- Summary (if available) -->
  {#if summary}
    <div class="alert bg-base-200 border-base-300 mb-8">
      <span class="material-symbols-outlined text-primary">info</span>
      <div class="flex-1">
        <p class="text-base-content/90">{summary}</p>
      </div>
    </div>
  {/if}

  <!-- Day-by-Day Itinerary -->
  <div class="space-y-6">
    {#each days as day (day.day_number)}
      {@const { morning, afternoon, evening } = getActivitiesByTimeSlot(day)}
      <div class="card bg-base-200 border border-base-300">
        <div class="card-body">
          <!-- Day Header -->
          <div class="flex items-center justify-between mb-4">
            <div>
              <h2 class="text-2xl font-bold text-white">
                Day {day.day_number}
                {#if day.title}
                  <span class="text-primary">- {day.title}</span>
                {/if}
              </h2>
              {#if day.date}
                <p class="text-sm text-base-content/60 mt-1">{day.date}</p>
              {/if}
            </div>
            <div class="badge badge-outline badge-lg">
              {formatCost(day.total_cost)}
            </div>
          </div>

          <!-- Timeline -->
          <div class="space-y-6">
            <!-- Morning Activities -->
            {#if morning.length > 0}
              <div class="flex gap-4">
                <div
                  class="flex flex-col items-center gap-2 pt-2 flex-shrink-0"
                >
                  <div
                    class="flex items-center justify-center w-10 h-10 rounded-full bg-warning/20 text-warning"
                  >
                    <span class="material-symbols-outlined text-xl"
                      >{getTimeSlotIcon("morning")}</span
                    >
                  </div>
                  <div class="w-0.5 h-full bg-base-300 min-h-[80px]"></div>
                </div>
                <div class="flex-1 space-y-3">
                  <h3 class="text-lg font-bold text-warning">
                    {getTimeSlotLabel("morning")}
                  </h3>
                  {#each morning as activity}
                    <ActivityCard {activity} />
                  {/each}
                </div>
              </div>
            {/if}

            <!-- Afternoon Activities -->
            {#if afternoon.length > 0}
              <div class="flex gap-4">
                <div
                  class="flex flex-col items-center gap-2 pt-2 flex-shrink-0"
                >
                  <div
                    class="flex items-center justify-center w-10 h-10 rounded-full bg-primary/20 text-primary"
                  >
                    <span class="material-symbols-outlined text-xl"
                      >{getTimeSlotIcon("afternoon")}</span
                    >
                  </div>
                  <div class="w-0.5 h-full bg-base-300 min-h-[80px]"></div>
                </div>
                <div class="flex-1 space-y-3">
                  <h3 class="text-lg font-bold text-primary">
                    {getTimeSlotLabel("afternoon")}
                  </h3>
                  {#each afternoon as activity}
                    <ActivityCard {activity} />
                  {/each}
                </div>
              </div>
            {/if}

            <!-- Evening Activities -->
            {#if evening.length > 0}
              <div class="flex gap-4">
                <div
                  class="flex flex-col items-center gap-2 pt-2 flex-shrink-0"
                >
                  <div
                    class="flex items-center justify-center w-10 h-10 rounded-full bg-secondary/20 text-secondary"
                  >
                    <span class="material-symbols-outlined text-xl"
                      >{getTimeSlotIcon("evening")}</span
                    >
                  </div>
                </div>
                <div class="flex-1 space-y-3">
                  <h3 class="text-lg font-bold text-secondary">
                    {getTimeSlotLabel("evening")}
                  </h3>
                  {#each evening as activity}
                    <ActivityCard {activity} />
                  {/each}
                </div>
              </div>
            {/if}
          </div>
        </div>
      </div>
    {/each}
  </div>

  <!-- Footer Summary -->
  <div class="card bg-primary/10 border border-primary/20 mt-8">
    <div class="card-body">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-3">
          <span class="material-symbols-outlined text-4xl text-primary"
            >payments</span
          >
          <div>
            <h3 class="text-2xl font-bold text-white">
              Total Estimated Cost
            </h3>
            <p class="text-sm text-base-content/60">
              Per person for {tripLengthDays}-day trip
            </p>
          </div>
        </div>
        <div class="text-4xl font-black text-primary">
          {formatCost(data.itinerary.total_cost || 0)}
        </div>
      </div>
    </div>
  </div>
</div>

<!-- Finalize Modal -->
{#if showFinalizeModal}
  <div class="modal modal-open">
    <div class="modal-box max-w-lg">
      <h3 class="font-bold text-2xl mb-4 flex items-center gap-2">
        <span class="material-symbols-outlined text-warning">warning</span>
        Finalize Itinerary?
      </h3>

      <div class="space-y-4">
        <p class="text-base-content/80">
          Finalizing this itinerary will:
        </p>
        <ul class="list-disc list-inside space-y-2 text-base-content/70 pl-2">
          <li>Lock the itinerary, making it read-only for all members</li>
          <li>Prevent any further modifications or regeneration</li>
          <li>Mark the trip as complete</li>
        </ul>
        <div class="alert alert-info">
          <span class="material-symbols-outlined">info</span>
          <span
            >This action cannot be undone. Make sure everyone is happy with the
            itinerary before finalizing.</span
          >
        </div>

        {#if form?.error}
          <div class="alert alert-error">
            <span class="material-symbols-outlined">error</span>
            <span>{form.error}</span>
          </div>
        {/if}
      </div>

      <form
        method="POST"
        action="?/finalize"
        use:enhance={() => {
          isSubmitting = true
          return async ({ update }) => {
            await update()
            isSubmitting = false
            if (!form?.error) {
              closeFinalizeModal()
              // Reload page to show finalized state
              window.location.reload()
            }
          }
        }}
      >
        <div class="modal-action">
          <button
            type="button"
            class="btn btn-ghost"
            onclick={closeFinalizeModal}
            disabled={isSubmitting}
          >
            Cancel
          </button>
          <button
            type="submit"
            class="btn btn-success gap-2"
            disabled={isSubmitting}
          >
            {#if isSubmitting}
              <span class="loading loading-spinner loading-sm"></span>
              Finalizing...
            {:else}
              <span class="material-symbols-outlined">check_circle</span>
              Finalize Itinerary
            {/if}
          </button>
        </div>
      </form>
    </div>
    <button
      type="button"
      class="modal-backdrop"
      onclick={closeFinalizeModal}
      aria-label="Close modal"
    ></button>
  </div>
{/if}
