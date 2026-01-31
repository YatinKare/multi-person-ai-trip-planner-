<script lang="ts">
  import type { PageData } from "./$types"
  import DestinationSelectionModal from "$lib/components/DestinationSelectionModal.svelte"

  interface Props {
    data: PageData
  }

  let { data }: Props = $props()

  // Type for destination from recommendations
  interface Destination {
    name: string
    region: string
    reasoning: string
    cost_per_person: number
    match_percentage?: number
    highlights: Array<{
      day: number
      description: string
    }>
    tradeoffs?: string
    image_url?: string
  }

  // Parse destinations from JSONB
  const destinations: Destination[] =
    (data.recommendations?.destinations as unknown as Destination[]) || []

  // Get members who have submitted preferences
  const respondedMembers =
    data.members?.filter(
      (m: { has_preferences: boolean }) => m.has_preferences,
    ) || []

  // Modal state
  let showSelectionModal = $state(false)
  let selectedDestinationIndex = $state<number>(0)
  let selectedDestinationName = $state<string>("")

  function openSelectionModal(index: number, name: string) {
    selectedDestinationIndex = index
    selectedDestinationName = name
    showSelectionModal = true
  }

  // Check if a destination has been selected (trip status is planning or beyond)
  const isDestinationSelected = data.trip.status === "planning" || data.trip.status === "finalized"
  const selectedIndex = data.recommendations?.selected_destination_index
</script>

<svelte:head>
  <title>Recommendations - {data.trip.name} - TripSync</title>
</svelte:head>

<div class="max-w-7xl mx-auto py-6 px-4 md:px-8 lg:px-16">
  {#if !data.recommendations || destinations.length === 0}
    <!-- No Recommendations State (could be error or not generated yet) -->
    {@const hasError = data.trip.status === 'recommending' && !data.recommendations}
    <div class="card bg-base-200 border {hasError ? 'border-error' : 'border-base-300'}">
      <div class="card-body items-center text-center py-16">
        {#if hasError}
          <!-- Error State -->
          <span class="material-symbols-outlined text-6xl text-error mb-4"
            >error</span
          >
          <h2 class="text-2xl font-bold text-white mb-2">
            Recommendation Generation Failed
          </h2>
          <div class="text-base-content/60 max-w-md mb-6">
            <p class="mb-2">An error occurred while generating destination recommendations. This could be due to:</p>
            <ul class="list-disc list-inside text-sm">
              <li>Conflicting group preferences that are impossible to satisfy</li>
              <li>Temporary AI service issues</li>
              <li>Network connectivity problems</li>
            </ul>
          </div>
          <div class="flex gap-3">
            <a href="/trips/{data.trip.id}" class="btn btn-primary">
              <span class="material-symbols-outlined">arrow_back</span>
              Back to Dashboard
            </a>
            {#if data.userRole === 'organizer'}
              <button
                class="btn btn-error"
                onclick={() => window.location.href = `/trips/${data.trip.id}#retry-recommendations`}
              >
                <span class="material-symbols-outlined">refresh</span>
                Try Again
              </button>
            {/if}
          </div>
        {:else}
          <!-- Not Generated Yet State -->
          <span class="material-symbols-outlined text-6xl text-primary mb-4"
            >travel_explore</span
          >
          <h2 class="text-2xl font-bold text-white mb-2">
            No Recommendations Yet
          </h2>
          <p class="text-base-content/60 max-w-md mb-6">
            Recommendations haven't been generated for this trip yet. The
            organizer can generate them from the trip dashboard.
          </p>
          <a href="/trips/{data.trip.id}" class="btn btn-primary">
            <span class="material-symbols-outlined">arrow_back</span>
            Back to Dashboard
          </a>
        {/if}
      </div>
    </div>
  {:else}
    <!-- Show warning if fewer than 3 destinations -->
    {#if destinations.length < 3}
      <div class="alert alert-warning mb-6">
        <span class="material-symbols-outlined">warning</span>
        <div>
          <h3 class="font-bold">Limited Recommendations</h3>
          <div class="text-sm">
            Only {destinations.length} destination{destinations.length === 1 ? '' : 's'} could be generated based on your group's preferences.
            This may indicate conflicting constraints or limited options.
          </div>
        </div>
      </div>
    {/if}

    <!-- Page Header -->
    <div
      class="w-full flex flex-col md:flex-row justify-between items-start md:items-center gap-6 mb-10 border-b border-base-300 pb-6"
    >
      <div class="flex flex-col gap-2">
        <h1 class="text-3xl md:text-4xl font-black tracking-tight">
          {data.trip.name}
        </h1>
        <div class="flex items-center gap-2">
          <span class="material-symbols-outlined text-primary text-sm"
            >auto_awesome</span
          >
          <p class="text-base-content/60 text-base">
            AI-Suggested Destinations based on your group's preferences.
          </p>
        </div>
      </div>

      <!-- Voting Members -->
      <div class="flex flex-col items-end gap-2">
        <span class="badge {isDestinationSelected ? 'badge-primary' : 'badge-ghost'} text-xs">
          {isDestinationSelected ? 'Destination Selected' : 'Voting In Progress'}
        </span>
        <div class="avatar-group -space-x-3">
          {#each respondedMembers.slice(0, 4) as member}
            <div class="avatar">
              <div class="w-10">
                <img
                  src={member.avatar_url ||
                    `https://api.dicebear.com/7.x/initials/svg?seed=${member.full_name || "User"}`}
                  alt={member.full_name || "User"}
                />
              </div>
            </div>
          {/each}
          {#if respondedMembers.length > 4}
            <div class="avatar placeholder">
              <div class="bg-base-300 w-10">
                <span class="text-xs font-bold"
                  >+{respondedMembers.length - 4}</span
                >
              </div>
            </div>
          {/if}
        </div>
      </div>
    </div>

    <!-- Destination Cards Grid -->
    <div
      class="w-full grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6 lg:gap-8 mb-20"
    >
      {#each destinations as destination, index}
        {@const upvotes = data.voteCounts[index]?.upvotes || 0}
        {@const downvotes = data.voteCounts[index]?.downvotes || 0}
        {@const userVote = data.userVotes[index]}
        <div
          class="card bg-base-200 border border-base-300 hover:border-primary/50 transition-all duration-300 shadow-lg overflow-hidden group"
        >
          <!-- Top Badge -->
          {#if destination.match_percentage}
            <div class="absolute top-4 right-4 z-10">
              <div
                class="badge {destination.match_percentage >= 95
                  ? 'badge-primary'
                  : 'badge-ghost'} gap-1.5"
              >
                <span class="material-symbols-outlined text-sm">verified</span>
                {destination.match_percentage}% MATCH
              </div>
            </div>
          {/if}

          <!-- Image -->
          <figure class="relative h-64 w-full overflow-hidden">
            <div
              class="absolute inset-0 bg-gradient-to-t from-base-200 to-transparent opacity-60 z-[1]"
            ></div>
            <div
              class="w-full h-full bg-center bg-cover transition-transform duration-700 group-hover:scale-105"
              style="background-image: url('{destination.image_url ||
                'https://images.unsplash.com/photo-1488646953014-85cb44e25828?w=800'}');"
            ></div>
            <div class="absolute bottom-4 left-4 z-10">
              <h3 class="text-2xl font-bold drop-shadow-md">
                {destination.name}
              </h3>
            </div>
          </figure>

          <!-- Content -->
          <div class="card-body p-5 gap-5">
            <!-- Cost & AI Reasoning -->
            <div class="space-y-3">
              <div
                class="flex justify-between items-center pb-3 border-b border-base-300"
              >
                <span class="text-base-content/60 text-sm"
                  >Est. Cost per person</span
                >
                <span class="text-primary text-xl font-bold"
                  >${destination.cost_per_person.toLocaleString()}</span
                >
              </div>
              <div
                class="bg-base-300/30 rounded-lg p-3 border border-base-300/50"
              >
                <div class="flex gap-2 mb-1">
                  <span class="material-symbols-outlined text-primary text-lg"
                    >psychology</span
                  >
                  <span class="text-xs font-bold uppercase tracking-wider"
                    >Why it fits</span
                  >
                </div>
                <p class="text-base-content/60 text-sm">
                  {destination.reasoning}
                </p>
              </div>
            </div>

            <!-- Highlights -->
            <div class="space-y-2">
              <p class="text-sm font-semibold">2-Day Highlight</p>
              <ul class="steps steps-vertical text-sm">
                {#each destination.highlights.slice(0, 2) as highlight}
                  <li class="step step-primary">
                    <div class="text-left">
                      <span class="font-medium">Day {highlight.day}:</span>
                      <span class="text-base-content/60"
                        >{highlight.description}</span
                      >
                    </div>
                  </li>
                {/each}
              </ul>
            </div>

            <!-- Actions -->
            <div class="card-actions flex-col gap-3 pt-2">
              <!-- Voting -->
              <div class="flex gap-3 w-full">
                <form method="POST" action="?/vote" class="flex-1">
                  <input
                    type="hidden"
                    name="recommendation_id"
                    value={data.recommendations.id}
                  />
                  <input
                    type="hidden"
                    name="destination_index"
                    value={index}
                  />
                  <input type="hidden" name="vote_type" value="upvote" />
                  <button
                    type="submit"
                    disabled={isDestinationSelected}
                    class="btn {userVote === 'upvote'
                      ? 'btn-primary'
                      : 'btn-ghost bg-base-300'} w-full gap-2"
                  >
                    <span
                      class="material-symbols-outlined {userVote === 'upvote'
                        ? ''
                        : 'text-base-content/60'}"
                      style={userVote === "upvote"
                        ? "font-variation-settings: 'FILL' 1"
                        : ""}
                    >
                      thumb_up
                    </span>
                    <span class="font-bold">{upvotes}</span>
                  </button>
                </form>
                <form method="POST" action="?/vote" class="flex-1">
                  <input
                    type="hidden"
                    name="recommendation_id"
                    value={data.recommendations.id}
                  />
                  <input
                    type="hidden"
                    name="destination_index"
                    value={index}
                  />
                  <input type="hidden" name="vote_type" value="downvote" />
                  <button
                    type="submit"
                    disabled={isDestinationSelected}
                    class="btn {userVote === 'downvote'
                      ? 'btn-error'
                      : 'btn-ghost bg-base-300'} w-full gap-2"
                  >
                    <span
                      class="material-symbols-outlined {userVote === 'downvote'
                        ? ''
                        : 'text-base-content/60'}"
                      style={userVote === "downvote"
                        ? "font-variation-settings: 'FILL' 1"
                        : ""}
                    >
                      thumb_down
                    </span>
                    <span class="font-bold">{downvotes}</span>
                  </button>
                </form>
              </div>

              <!-- Organizer Select (visible only to organizers) -->
              {#if data.userRole === "organizer"}
                {#if isDestinationSelected && selectedIndex === index}
                  <div class="w-full p-4 bg-primary/10 border-2 border-primary rounded-lg text-center">
                    <span class="material-symbols-outlined text-primary text-2xl" style="font-variation-settings: 'FILL' 1;">
                      check_circle
                    </span>
                    <p class="text-primary font-bold mt-2">Selected Destination</p>
                  </div>
                {:else if !isDestinationSelected}
                  <button
                    class="btn btn-primary w-full gap-2"
                    onclick={() => openSelectionModal(index, destination.name)}
                  >
                    <span class="material-symbols-outlined text-xl"
                      >check_circle</span
                    >
                    Select Final Destination
                  </button>
                {/if}
              {/if}
            </div>
          </div>
        </div>
      {/each}
    </div>

    <!-- Sticky Footer Action (placeholder for regeneration - P1 feature) -->
    <!-- <div class="fixed bottom-6 left-1/2 transform -translate-x-1/2 z-40 lg:left-[calc(50%+160px)]">
      <button class="btn btn-ghost bg-base-200 border border-base-300 gap-2 shadow-2xl hover:scale-105 transition-transform">
        <span class="material-symbols-outlined text-primary">autorenew</span>
        <span>Generate More Options</span>
      </button>
    </div> -->
  {/if}
</div>

<!-- Destination Selection Modal -->
<DestinationSelectionModal
  bind:open={showSelectionModal}
  destinationName={selectedDestinationName}
  destinationIndex={selectedDestinationIndex}
/>

<style>
  @import url("https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200");

  .material-symbols-outlined {
    font-variation-settings:
      "FILL" 0,
      "wght" 400,
      "GRAD" 0,
      "opsz" 24;
  }
</style>
