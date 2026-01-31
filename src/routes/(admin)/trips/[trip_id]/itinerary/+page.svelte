<script lang="ts">
  import type { PageData } from "./$types"

  interface Props {
    data: PageData
  }

  let { data }: Props = $props()

  // Type for activity in the itinerary
  interface Activity {
    name: string
    description: string
    time_slot: string
    estimated_cost: number
    location: string
    location_url?: string
    duration_hours: number
    tips?: string
    category?: string
  }

  // Type for day itinerary
  interface DayItinerary {
    day_number: number
    date?: string
    title?: string
    activities: Activity[]
    total_cost: number
  }

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
          onclick={() => {
            if (
              confirm(
                "Finalize this itinerary? This will lock it and make it read-only for all members.",
              )
            ) {
              // TODO: Implement finalization
              alert("Finalization feature coming soon!")
            }
          }}
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
                    <div class="card bg-base-300 border border-base-content/10">
                      <div class="card-body p-4">
                        <div class="flex justify-between items-start gap-4">
                          <div class="flex-1">
                            <h4 class="font-bold text-white">
                              {activity.name}
                            </h4>
                            <p class="text-sm text-base-content/70 mt-1">
                              {activity.description}
                            </p>
                            <div class="flex items-center gap-4 mt-3 text-sm">
                              <span class="flex items-center gap-1">
                                <span
                                  class="material-symbols-outlined text-xs text-primary"
                                  >location_on</span
                                >
                                {#if activity.location_url}
                                  <a
                                    href={activity.location_url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    class="link link-primary"
                                  >
                                    {activity.location}
                                  </a>
                                {:else}
                                  <span>{activity.location}</span>
                                {/if}
                              </span>
                              <span class="flex items-center gap-1">
                                <span
                                  class="material-symbols-outlined text-xs text-base-content/60"
                                  >schedule</span
                                >
                                {activity.duration_hours}h
                              </span>
                              {#if activity.category}
                                <span
                                  class="badge badge-xs badge-outline capitalize"
                                >
                                  {activity.category}
                                </span>
                              {/if}
                            </div>
                            {#if activity.tips}
                              <div
                                class="alert alert-info bg-info/10 border-info/20 mt-3 py-2"
                              >
                                <span
                                  class="material-symbols-outlined text-sm"
                                  >lightbulb</span
                                >
                                <span class="text-xs">{activity.tips}</span>
                              </div>
                            {/if}
                          </div>
                          <div class="badge badge-primary badge-lg">
                            {formatCost(activity.estimated_cost)}
                          </div>
                        </div>
                      </div>
                    </div>
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
                    <div class="card bg-base-300 border border-base-content/10">
                      <div class="card-body p-4">
                        <div class="flex justify-between items-start gap-4">
                          <div class="flex-1">
                            <h4 class="font-bold text-white">
                              {activity.name}
                            </h4>
                            <p class="text-sm text-base-content/70 mt-1">
                              {activity.description}
                            </p>
                            <div class="flex items-center gap-4 mt-3 text-sm">
                              <span class="flex items-center gap-1">
                                <span
                                  class="material-symbols-outlined text-xs text-primary"
                                  >location_on</span
                                >
                                {#if activity.location_url}
                                  <a
                                    href={activity.location_url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    class="link link-primary"
                                  >
                                    {activity.location}
                                  </a>
                                {:else}
                                  <span>{activity.location}</span>
                                {/if}
                              </span>
                              <span class="flex items-center gap-1">
                                <span
                                  class="material-symbols-outlined text-xs text-base-content/60"
                                  >schedule</span
                                >
                                {activity.duration_hours}h
                              </span>
                              {#if activity.category}
                                <span
                                  class="badge badge-xs badge-outline capitalize"
                                >
                                  {activity.category}
                                </span>
                              {/if}
                            </div>
                            {#if activity.tips}
                              <div
                                class="alert alert-info bg-info/10 border-info/20 mt-3 py-2"
                              >
                                <span
                                  class="material-symbols-outlined text-sm"
                                  >lightbulb</span
                                >
                                <span class="text-xs">{activity.tips}</span>
                              </div>
                            {/if}
                          </div>
                          <div class="badge badge-primary badge-lg">
                            {formatCost(activity.estimated_cost)}
                          </div>
                        </div>
                      </div>
                    </div>
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
                    <div class="card bg-base-300 border border-base-content/10">
                      <div class="card-body p-4">
                        <div class="flex justify-between items-start gap-4">
                          <div class="flex-1">
                            <h4 class="font-bold text-white">
                              {activity.name}
                            </h4>
                            <p class="text-sm text-base-content/70 mt-1">
                              {activity.description}
                            </p>
                            <div class="flex items-center gap-4 mt-3 text-sm">
                              <span class="flex items-center gap-1">
                                <span
                                  class="material-symbols-outlined text-xs text-primary"
                                  >location_on</span
                                >
                                {#if activity.location_url}
                                  <a
                                    href={activity.location_url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    class="link link-primary"
                                  >
                                    {activity.location}
                                  </a>
                                {:else}
                                  <span>{activity.location}</span>
                                {/if}
                              </span>
                              <span class="flex items-center gap-1">
                                <span
                                  class="material-symbols-outlined text-xs text-base-content/60"
                                  >schedule</span
                                >
                                {activity.duration_hours}h
                              </span>
                              {#if activity.category}
                                <span
                                  class="badge badge-xs badge-outline capitalize"
                                >
                                  {activity.category}
                                </span>
                              {/if}
                            </div>
                            {#if activity.tips}
                              <div
                                class="alert alert-info bg-info/10 border-info/20 mt-3 py-2"
                              >
                                <span
                                  class="material-symbols-outlined text-sm"
                                  >lightbulb</span
                                >
                                <span class="text-xs">{activity.tips}</span>
                              </div>
                            {/if}
                          </div>
                          <div class="badge badge-primary badge-lg">
                            {formatCost(activity.estimated_cost)}
                          </div>
                        </div>
                      </div>
                    </div>
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
