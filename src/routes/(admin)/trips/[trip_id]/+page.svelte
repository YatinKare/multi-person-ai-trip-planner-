<script lang="ts">
  import DeleteTripModal from "$lib/components/DeleteTripModal.svelte"
  import LeaveTripModal from "$lib/components/LeaveTripModal.svelte"
  import AggregatedPreferences from "$lib/components/AggregatedPreferences.svelte"
  import { page } from "$app/state"
  import { goto } from "$app/navigation"
  import type { PageData } from "./$types"

  interface Props {
    data: PageData
  }

  let { data }: Props = $props()

  // Get badge class based on trip status
  function getStatusBadgeClass(status: string): string {
    const badges: Record<string, string> = {
      collecting: "badge-warning",
      recommending: "badge-info",
      voting: "badge-info",
      planning: "badge-info",
      finalized: "badge-success",
    }
    return badges[status] || "badge-neutral"
  }

  // Get status display text
  function getStatusText(status: string): string {
    const texts: Record<string, string> = {
      collecting: "Collecting Preferences",
      recommending: "AI Thinking",
      voting: "Voting",
      planning: "Planning",
      finalized: "Finalized",
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

    if (diffMins < 1) return "just now"
    if (diffMins < 60) return `${diffMins}m ago`
    if (diffHours < 24) return `${diffHours}h ago`
    if (diffDays < 7) return `${diffDays}d ago`
    return new Date(dateString).toLocaleDateString()
  }

  // Copy invite link to clipboard
  async function copyInviteLink() {
    const inviteUrl = `${page.url.origin}/join/${data.trip.invite_code}`
    try {
      await navigator.clipboard.writeText(inviteUrl)
      showCopySuccess = true
      setTimeout(() => (showCopySuccess = false), 2000)
    } catch (err) {
      console.error("Failed to copy:", err)
    }
  }

  // Check if there are warnings before generating recommendations
  function checkAndGenerateRecommendations() {
    const hasWarnings =
      data.responseCount < 2 ||
      data.aggregated?.conflicts?.noDateOverlap ||
      data.aggregated?.conflicts?.noBudgetOverlap

    if (hasWarnings) {
      showRecommendationWarningModal = true
    } else {
      generateRecommendations()
    }
  }

  // Generate recommendations via FastAPI backend
  async function generateRecommendations() {
    if (!canGenerateRecommendations || generatingRecommendations) return

    // Close modal if it was open
    showRecommendationWarningModal = false

    generatingRecommendations = true
    recommendationError = null // Clear previous errors
    retryAttempt++

    try {
      // Get the Supabase session token
      const {
        data: { session },
      } = await data.supabase.auth.getSession()

      if (!session) {
        recommendationError = "Your session has expired. Please refresh the page and try again."
        return
      }

      // Call FastAPI backend with timeout
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 120000) // 2 minute timeout

      const response = await fetch(
        `http://localhost:8000/api/trips/${data.trip.id}/recommendations`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${session.access_token}`,
          },
          signal: controller.signal,
        },
      )

      clearTimeout(timeoutId)

      if (!response.ok) {
        const error = await response.json().catch(() => ({}))

        // Provide more specific error messages based on status code
        if (response.status === 400) {
          throw new Error(error.detail || "Invalid trip status or preferences. Please check your group's preferences.")
        } else if (response.status === 403) {
          throw new Error("You don't have permission to generate recommendations for this trip.")
        } else if (response.status === 404) {
          throw new Error("Trip not found. Please refresh the page.")
        } else if (response.status === 500) {
          throw new Error(error.detail || "AI service error. This could be due to conflicting preferences or temporary service issues.")
        } else {
          throw new Error(error.detail || "Failed to generate recommendations. Please try again.")
        }
      }

      const result = await response.json()

      // Check if we got valid recommendations
      if (!result.destinations || result.destinations.length === 0) {
        throw new Error("No destinations could be generated. Your group's preferences may be too restrictive or conflicting.")
      }

      // Success - redirect to recommendations page
      window.location.href = `/trips/${data.trip.id}/recommendations`
    } catch (err) {
      console.error("Error generating recommendations:", err)

      if (err instanceof Error) {
        if (err.name === 'AbortError') {
          recommendationError = "Request timed out. The AI is taking longer than expected. Please try again."
        } else if (err.message.includes('fetch')) {
          recommendationError = "Network error. Please check your connection and try again."
        } else {
          recommendationError = err.message
        }
      } else {
        recommendationError = "An unexpected error occurred. Please try again."
      }

      // Log detailed error for debugging
      console.error("Generation attempt:", retryAttempt, "Error:", err)
    } finally {
      generatingRecommendations = false
    }
  }

  let showCopySuccess = $state(false)
  let showDeleteModal = $state(false)
  let showLeaveModal = $state(false)
  let showRecommendationWarningModal = $state(false)
  let isOrganizer = $derived(data.userRole === "organizer")
  let generatingRecommendations = $state(false)
  let recommendationError = $state<string | null>(null)
  let retryAttempt = $state(0)

  // Can generate recommendations if:
  // 1. User is organizer
  // 2. At least 1 member has submitted preferences
  // 3. Recommendations haven't been generated yet
  let canGenerateRecommendations = $derived(
    isOrganizer && data.responseCount > 0 && !data.hasRecommendations,
  )

  // Clear error when user dismisses
  function dismissError() {
    recommendationError = null
  }

  // Generate itinerary via FastAPI backend
  async function generateItinerary() {
    if (!data.selectedDestination || generatingItinerary) return

    generatingItinerary = true
    itineraryError = null // Clear previous errors
    itineraryRetryAttempt++

    try {
      // Get the Supabase session token
      const {
        data: { session },
      } = await data.supabase.auth.getSession()

      if (!session) {
        itineraryError = "Your session has expired. Please refresh the page and try again."
        return
      }

      // Call FastAPI backend with timeout
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 120000) // 2 minute timeout

      const response = await fetch(
        `http://localhost:8000/api/ai/itinerary/generate`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${session.access_token}`,
          },
          body: JSON.stringify({
            trip_id: data.trip.id,
            destination_name: data.selectedDestination.destination_name,
          }),
          signal: controller.signal,
        },
      )

      clearTimeout(timeoutId)

      if (!response.ok) {
        const error = await response.json().catch(() => ({}))

        // Provide more specific error messages based on status code
        if (response.status === 400) {
          throw new Error(error.detail || "Invalid trip status. Trip must be in 'planning' status with a destination selected.")
        } else if (response.status === 403) {
          throw new Error("You don't have permission to generate an itinerary for this trip.")
        } else if (response.status === 404) {
          throw new Error("Trip not found. Please refresh the page.")
        } else if (response.status === 500) {
          throw new Error(error.detail || "AI service error. This could be due to conflicting preferences or temporary service issues.")
        } else {
          throw new Error(error.detail || "Failed to generate itinerary. Please try again.")
        }
      }

      const result = await response.json()

      // Check if we got valid itinerary
      if (!result.days || result.days.length === 0) {
        throw new Error("No itinerary could be generated. Please try again.")
      }

      // Success - redirect to itinerary page
      window.location.href = `/trips/${data.trip.id}/itinerary`
    } catch (err) {
      console.error("Error generating itinerary:", err)

      if (err instanceof Error) {
        if (err.name === 'AbortError') {
          itineraryError = "Request timed out. The AI is taking longer than expected. Please try again."
        } else if (err.message.includes('fetch')) {
          itineraryError = "Network error. Please check your connection and try again."
        } else {
          itineraryError = err.message
        }
      } else {
        itineraryError = "An unexpected error occurred. Please try again."
      }

      // Log detailed error for debugging
      console.error("Generation attempt:", itineraryRetryAttempt, "Error:", err)
    } finally {
      generatingItinerary = false
    }
  }

  let generatingItinerary = $state(false)
  let itineraryError = $state<string | null>(null)
  let itineraryRetryAttempt = $state(0)

  // Clear itinerary error when user dismisses
  function dismissItineraryError() {
    itineraryError = null
  }

  // Nudge state
  let nudgingMembers = $state<Set<string>>(new Set())
  let nudgeSuccess = $state<string | null>(null)
  let nudgeError = $state<string | null>(null)

  // Check if member can be nudged (24 hour throttle)
  function canNudgeMember(member: any): boolean {
    if (!member.nudged_at) return true

    const lastNudged = new Date(member.nudged_at)
    const now = new Date()
    const hoursSinceLastNudge = (now.getTime() - lastNudged.getTime()) / (1000 * 60 * 60)

    return hoursSinceLastNudge >= 24
  }

  // Nudge a member
  async function nudgeMember(memberUserId: string) {
    if (nudgingMembers.has(memberUserId)) return

    nudgingMembers = new Set(nudgingMembers).add(memberUserId)
    nudgeError = null
    nudgeSuccess = null

    try {
      const formData = new FormData()
      formData.append('member_user_id', memberUserId)

      const response = await fetch(`/trips/${data.trip.id}?/nudgeMember`, {
        method: 'POST',
        body: formData
      })

      const result = await response.json()

      if (result.type === 'success') {
        nudgeSuccess = result.data.message
        // Refresh page to update nudged_at timestamp
        setTimeout(() => {
          window.location.reload()
        }, 1500)
      } else if (result.type === 'failure') {
        nudgeError = result.data.message
      } else {
        nudgeError = 'Failed to send nudge. Please try again.'
      }
    } catch (err) {
      console.error('Error nudging member:', err)
      nudgeError = 'Network error. Please try again.'
    } finally {
      const newSet = new Set(nudgingMembers)
      newSet.delete(memberUserId)
      nudgingMembers = newSet
    }
  }

  // Clear nudge messages
  function dismissNudgeMessages() {
    nudgeSuccess = null
    nudgeError = null
  }
</script>

<svelte:head>
  <title>{data.trip.name} - TripSync</title>
</svelte:head>

<div class="max-w-7xl mx-auto">
  <!-- Breadcrumbs -->
  <nav class="mb-4 flex items-center text-sm font-medium">
    <a
      class="text-base-content/60 hover:text-primary transition-colors"
      href="/trips">All Trips</a
    >
    <span class="mx-2 text-base-content/40">/</span>
    <span class="text-base-content font-bold">{data.trip.name}</span>
  </nav>

  <!-- Heading Section -->
  <div
    class="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-8"
  >
    <div class="flex flex-col gap-2">
      <h1 class="text-4xl md:text-5xl font-black text-white tracking-tight">
        {data.trip.name}
      </h1>
      <div class="flex items-center gap-3 mt-1">
        <span
          class="{getStatusBadgeClass(
            data.trip.status,
          )} gap-2 p-3 font-bold bg-warning/10 border-warning/20 text-warning"
        >
          <span class="size-2 rounded-full bg-warning animate-pulse"></span>
          {getStatusText(data.trip.status)}
        </span>
        <span class="text-base-content/60 text-sm font-medium">
          {data.responseCount} of {data.totalMembers} Responded
        </span>
      </div>
    </div>
    <div class="flex flex-wrap gap-3">
      {#if isOrganizer}
        {#if data.hasRecommendations}
          <a
            href="/trips/{data.trip.id}/recommendations"
            class="btn btn-primary flex items-center gap-2 text-base-300 font-bold hover:shadow-[0_0_20px_rgba(19,236,182,0.3)]"
          >
            <span class="material-symbols-outlined">travel_explore</span>
            View Recommendations
          </a>
        {:else}
          <button
            class="btn btn-primary flex items-center gap-2 text-base-300 font-bold hover:shadow-[0_0_20px_rgba(19,236,182,0.3)]"
            disabled={!canGenerateRecommendations || generatingRecommendations}
            onclick={() => checkAndGenerateRecommendations()}
          >
            {#if generatingRecommendations}
              <span class="loading loading-spinner loading-sm"></span>
              Generating...
            {:else}
              <span class="material-symbols-outlined">auto_awesome</span>
              Generate Recommendations
            {/if}
          </button>
        {/if}
        <button
          onclick={() => goto(`/trips/${data.trip.id}/preferences`)}
          class="btn btn-neutral flex items-center gap-2 font-bold"
        >
          <span class="material-symbols-outlined">tune</span>
          My Preferences
        </button>
        <div class="dropdown dropdown-end">
          <button tabindex="0" class="btn btn-ghost flex items-center gap-2">
            <span class="material-symbols-outlined">more_vert</span>
          </button>
          <ul
            class="dropdown-content menu p-2 shadow-lg bg-base-200 rounded-box w-52 border border-base-300"
          >
            <li>
              <button class="flex items-center gap-2">
                <span class="material-symbols-outlined text-lg">edit</span>
                Edit Trip
              </button>
            </li>
            <li>
              <button
                class="flex items-center gap-2 text-error hover:bg-error/10"
                onclick={() => (showDeleteModal = true)}
              >
                <span class="material-symbols-outlined text-lg">delete</span>
                Delete Trip
              </button>
            </li>
          </ul>
        </div>
      {:else}
        <button
          onclick={() => goto(`/trips/${data.trip.id}/preferences`)}
          class="btn btn-primary flex items-center gap-2 text-base-300 font-bold hover:shadow-[0_0_20px_rgba(19,236,182,0.3)]"
        >
          <span class="material-symbols-outlined">tune</span>
          My Preferences
        </button>
        <div class="dropdown dropdown-end">
          <button tabindex="0" class="btn btn-ghost flex items-center gap-2">
            <span class="material-symbols-outlined">more_vert</span>
          </button>
          <ul
            class="dropdown-content menu p-2 shadow-lg bg-base-200 rounded-box w-52 border border-base-300"
          >
            <li>
              <button
                class="flex items-center gap-2 text-warning hover:bg-warning/10"
                onclick={() => (showLeaveModal = true)}
              >
                <span class="material-symbols-outlined text-lg">logout</span>
                Leave Trip
              </button>
            </li>
          </ul>
        </div>
      {/if}
    </div>
  </div>

  <!-- Error Banner -->
  {#if recommendationError}
    <div role="alert" class="alert alert-error mb-8 shadow-lg">
      <span class="material-symbols-outlined text-2xl">error</span>
      <div class="flex-1">
        <h3 class="font-bold">Failed to Generate Recommendations</h3>
        <div class="text-sm mt-1">{recommendationError}</div>
      </div>
      <div class="flex gap-2">
        <button
          class="btn btn-sm btn-ghost"
          onclick={dismissError}
        >
          Dismiss
        </button>
        {#if isOrganizer && canGenerateRecommendations}
          <button
            class="btn btn-sm btn-primary"
            onclick={() => generateRecommendations()}
            disabled={generatingRecommendations}
          >
            {#if generatingRecommendations}
              <span class="loading loading-spinner loading-xs"></span>
            {:else}
              <span class="material-symbols-outlined text-sm">refresh</span>
            {/if}
            Retry
          </button>
        {/if}
      </div>
    </div>
  {/if}

  {#if itineraryError}
    <div role="alert" class="alert alert-error mb-8 shadow-lg">
      <span class="material-symbols-outlined text-2xl">error</span>
      <div class="flex-1">
        <h3 class="font-bold">Failed to Generate Itinerary</h3>
        <div class="text-sm mt-1">{itineraryError}</div>
      </div>
      <div class="flex gap-2">
        <button
          class="btn btn-sm btn-ghost"
          onclick={dismissItineraryError}
        >
          Dismiss
        </button>
        {#if isOrganizer && data.selectedDestination}
          <button
            class="btn btn-sm btn-primary"
            onclick={() => generateItinerary()}
            disabled={generatingItinerary}
          >
            {#if generatingItinerary}
              <span class="loading loading-spinner loading-xs"></span>
            {:else}
              <span class="material-symbols-outlined text-sm">refresh</span>
            {/if}
            Retry
          </button>
        {/if}
      </div>
    </div>
  {/if}

  <!-- Nudge Success Banner -->
  {#if nudgeSuccess}
    <div role="alert" class="alert alert-success mb-8 shadow-lg">
      <span class="material-symbols-outlined text-2xl">check_circle</span>
      <div class="flex-1">
        <h3 class="font-bold">Nudge Sent!</h3>
        <div class="text-sm mt-1">{nudgeSuccess}</div>
      </div>
      <button
        class="btn btn-sm btn-ghost"
        onclick={dismissNudgeMessages}
      >
        Dismiss
      </button>
    </div>
  {/if}

  <!-- Nudge Error Banner -->
  {#if nudgeError}
    <div role="alert" class="alert alert-error mb-8 shadow-lg">
      <span class="material-symbols-outlined text-2xl">error</span>
      <div class="flex-1">
        <h3 class="font-bold">Failed to Send Nudge</h3>
        <div class="text-sm mt-1">{nudgeError}</div>
      </div>
      <button
        class="btn btn-sm btn-ghost"
        onclick={dismissNudgeMessages}
      >
        Dismiss
      </button>
    </div>
  {/if}

  <!-- Edge Case Warning Banners -->
  {#if data.trip.status === 'collecting' && data.totalMembers === 1 && isOrganizer}
    <div role="alert" class="alert alert-warning mb-8 shadow-lg">
      <span class="material-symbols-outlined text-2xl">group_add</span>
      <div class="flex-1">
        <h3 class="font-bold">You're Planning Solo!</h3>
        <div class="text-sm mt-1">
          You're the only member of this trip. Share the invite link below to collect preferences from your travel companions.
        </div>
      </div>
    </div>
  {/if}

  {#if data.trip.status === 'collecting' && data.responseCount === 0 && data.totalMembers > 1 && isOrganizer}
    <div role="alert" class="alert alert-info mb-8 shadow-lg">
      <span class="material-symbols-outlined text-2xl">pending</span>
      <div class="flex-1">
        <h3 class="font-bold">Waiting for Responses</h3>
        <div class="text-sm mt-1">
          None of your {data.totalMembers - 1} invited members have submitted their preferences yet. You can still generate recommendations once at least one person responds.
        </div>
      </div>
    </div>
  {/if}

  {#if data.aggregated?.conflicts && isOrganizer && !data.hasRecommendations}
    {#if data.aggregated.conflicts.noDateOverlap}
      <div role="alert" class="alert alert-warning mb-8 shadow-lg">
        <span class="material-symbols-outlined text-2xl">event_busy</span>
        <div class="flex-1">
          <h3 class="font-bold">Date Conflict Detected</h3>
          <div class="text-sm mt-1">
            {data.aggregated.conflicts.details?.find(d => d.includes('date'))  || 'No overlapping dates between all members'}.
            You may want to ask members to expand their date ranges, or proceed with a subset of the group.
          </div>
        </div>
      </div>
    {/if}
    {#if data.aggregated.conflicts.noBudgetOverlap}
      <div role="alert" class="alert alert-warning mb-8 shadow-lg">
        <span class="material-symbols-outlined text-2xl">payments</span>
        <div class="flex-1">
          <h3 class="font-bold">Budget Conflict Detected</h3>
          <div class="text-sm mt-1">
            {data.aggregated.conflicts.details?.find(d => d.includes('budget') || d.includes('Budget')) || 'Budget ranges don\'t overlap between members'}.
            Consider discussing budget expectations before generating recommendations.
          </div>
        </div>
      </div>
    {/if}
    {#if data.aggregated.conflicts.noCommonVibes}
      <div role="alert" class="alert alert-info mb-8 shadow-lg">
        <span class="material-symbols-outlined text-2xl">explore</span>
        <div class="flex-1">
          <h3 class="font-bold">No Common Vibes</h3>
          <div class="text-sm mt-1">
            No vibes were selected by all members. The AI will try to find destinations that balance everyone's preferences.
          </div>
        </div>
      </div>
    {/if}
  {/if}

  <!-- Invite Action Card -->
  {#if isOrganizer}
    <div
      class="relative overflow-hidden rounded-2xl bg-base-200 border border-base-300 mb-8"
    >
      <div
        class="absolute inset-0 z-0 opacity-40 mix-blend-overlay bg-cover bg-center"
      ></div>
      <div
        class="absolute inset-0 z-0 bg-gradient-to-r from-base-200 via-base-200/95 to-transparent"
      ></div>
      <div
        class="relative z-10 flex flex-col md:flex-row items-center justify-between p-6 md:p-8 gap-6"
      >
        <div class="flex flex-col gap-2 max-w-xl">
          <div class="flex items-center gap-2 text-primary mb-1">
            <span class="material-symbols-outlined">mail</span>
            <span class="text-sm font-bold uppercase tracking-wider"
              >Invite Friends</span
            >
          </div>
          <h2 class="text-2xl font-bold text-white">Get the gang together</h2>
          <p class="text-base-content/80">
            Share this unique link with your group to collect their preferences,
            budget, and availability automatically.
          </p>
        </div>
        <div
          class="w-full md:max-w-md bg-base-100/50 p-1.5 rounded-xl border border-base-300 flex items-center backdrop-blur-sm"
        >
          <div
            class="flex-1 px-3 py-2 text-base-content/80 font-mono text-sm truncate select-all"
          >
            {page.url.origin}/join/{data.trip.invite_code}
          </div>
          <button
            class="btn btn-primary btn-sm h-10 px-4 text-base-300 font-bold gap-2"
            onclick={copyInviteLink}
          >
            <span class="material-symbols-outlined text-[20px]">
              {showCopySuccess ? "check" : "content_copy"}
            </span>
            {showCopySuccess ? "Copied!" : "Copy Link"}
          </button>
        </div>
      </div>
    </div>
  {/if}

  <!-- Selected Destination Card -->
  {#if data.selectedDestination}
    <div
      class="relative overflow-hidden rounded-2xl bg-gradient-to-br from-primary/10 via-base-200 to-base-200 border-2 border-primary/30 mb-8"
    >
      <div
        class="absolute inset-0 z-0 opacity-20 bg-[radial-gradient(circle_at_50%_120%,rgba(19,236,182,0.2),transparent_50%)]"
      ></div>
      <div class="relative z-10 p-6 md:p-8">
        <div class="flex items-start justify-between gap-4 mb-4">
          <div class="flex items-center gap-3">
            <span
              class="material-symbols-outlined text-4xl text-primary"
              style="font-variation-settings: 'FILL' 1;"
            >
              location_on
            </span>
            <div>
              <span
                class="inline-block px-3 py-1 bg-primary/20 text-primary text-xs font-bold uppercase tracking-wider rounded-full mb-2"
              >
                Selected Destination
              </span>
              <h2 class="text-3xl font-bold text-white">
                {data.selectedDestination.name}
              </h2>
              <p class="text-base-content/60 text-sm mt-1">
                {data.selectedDestination.region}
              </p>
            </div>
          </div>
          <a
            href="/trips/{data.trip.id}/recommendations"
            class="btn btn-ghost btn-sm gap-2"
          >
            <span class="material-symbols-outlined">visibility</span>
            View All
          </a>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6">
          <div class="bg-base-200/50 rounded-xl p-4 border border-base-300/50">
            <div class="flex items-center gap-2 mb-3">
              <span class="material-symbols-outlined text-primary text-lg"
                >auto_awesome</span
              >
              <span class="text-sm font-bold text-base-content/80"
                >Why This Destination</span
              >
            </div>
            <p class="text-sm text-base-content/70">
              {data.selectedDestination.reasoning}
            </p>
          </div>

          <div class="bg-base-200/50 rounded-xl p-4 border border-base-300/50">
            <div class="flex items-center gap-2 mb-3">
              <span class="material-symbols-outlined text-primary text-lg"
                >payments</span
              >
              <span class="text-sm font-bold text-base-content/80"
                >Estimated Cost</span
              >
            </div>
            <p class="text-2xl font-bold text-primary">
              ${data.selectedDestination.cost_per_person.toLocaleString()}
              <span class="text-sm text-base-content/60 font-normal"
                >per person</span
              >
            </p>
          </div>
        </div>

        {#if data.trip.status === "planning" && data.userRole === "organizer"}
          <div class="mt-6 pt-6 border-t border-base-300/50">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2">
                <span class="material-symbols-outlined text-warning">info</span>
                <span class="text-sm text-base-content/70">
                  Ready to create your itinerary?
                </span>
              </div>
              <button
                class="btn btn-primary gap-2"
                disabled={generatingItinerary}
                onclick={() => generateItinerary()}
              >
                {#if generatingItinerary}
                  <span class="loading loading-spinner loading-sm"></span>
                  Generating...
                {:else}
                  <span class="material-symbols-outlined">auto_awesome</span>
                  Generate Itinerary
                {/if}
              </button>
            </div>
          </div>
        {/if}
      </div>
    </div>
  {/if}

  <!-- Dashboard Grid -->
  <div class="grid grid-cols-1 lg:grid-cols-12 gap-6 pb-12">
    <!-- Left Col: Member List -->
    <div class="lg:col-span-7 flex flex-col gap-4">
      <div class="flex items-center justify-between">
        <h3 class="text-lg font-bold text-white flex items-center gap-2">
          <span class="material-symbols-outlined text-primary">groups</span>
          Trip Members
        </h3>
      </div>
      <div
        class="bg-base-200 rounded-xl border border-base-300 overflow-hidden"
      >
        <div class="overflow-x-auto">
          <table class="table w-full">
            <thead>
              <tr class="border-b border-base-300 text-base-content/60">
                <th>Member</th>
                <th>Status</th>
                {#if isOrganizer}
                  <th class="text-right">Action</th>
                {/if}
              </tr>
            </thead>
            <tbody>
              {#each data.members as member (member.user_id)}
                <tr class="hover">
                  <td>
                    <div class="flex items-center gap-3">
                      {#if member.profile?.avatar_url}
                        <div class="avatar">
                          <div
                            class="w-10 rounded-full {member.role ===
                            'organizer'
                              ? 'ring-2 ring-primary/20'
                              : ''}"
                          >
                            <img
                              src={member.profile.avatar_url}
                              alt={member.profile.full_name || "User"}
                            />
                          </div>
                        </div>
                      {:else}
                        <div class="avatar placeholder">
                          <div
                            class="bg-neutral text-neutral-content rounded-full w-10"
                          >
                            <span class="text-xs">
                              {member.profile?.full_name
                                ?.split(" ")
                                .map((n: string) => n[0])
                                .join("")
                                .slice(0, 2) || "??"}
                            </span>
                          </div>
                        </div>
                      {/if}
                      <div>
                        <div class="font-bold">
                          {member.profile?.full_name || "Unknown"}
                          {#if member.user_id === data.userId}
                            <span class="text-xs text-base-content/60"
                              >(You)</span
                            >
                          {/if}
                        </div>
                        <div class="text-xs opacity-50">
                          {#if member.role === "organizer"}
                            Organizer
                          {:else}
                            Joined {getRelativeTime(member.joined_at)}
                          {/if}
                        </div>
                      </div>
                    </div>
                  </td>
                  <td>
                    {#if member.has_responded}
                      <div class="badge badge-primary badge-outline gap-1">
                        <span class="material-symbols-outlined text-[14px]"
                          >check_circle</span
                        >
                        Responded
                      </div>
                    {:else}
                      <div class="badge badge-warning badge-outline gap-1">
                        <span class="material-symbols-outlined text-[14px]"
                          >hourglass_empty</span
                        >
                        Pending
                      </div>
                    {/if}
                  </td>
                  {#if isOrganizer}
                    <td class="text-right">
                      {#if !member.has_responded && member.user_id !== data.userId}
                        {#if member.nudged_at && !canNudgeMember(member)}
                          <span class="text-xs text-base-content/60">
                            Nudged {getRelativeTime(member.nudged_at)}
                          </span>
                        {:else}
                          <button
                            class="btn btn-xs btn-neutral gap-1"
                            onclick={() => nudgeMember(member.user_id)}
                            disabled={nudgingMembers.has(member.user_id)}
                          >
                            {#if nudgingMembers.has(member.user_id)}
                              <span class="loading loading-spinner loading-xs"></span>
                              Sending...
                            {:else}
                              <span class="material-symbols-outlined text-[14px]"
                                >notifications_active</span
                              >
                              {member.nudged_at ? 'Nudge Again' : 'Nudge'}
                            {/if}
                          </button>
                        {/if}
                      {:else}
                        <span class="text-base-content/40">-</span>
                      {/if}
                    </td>
                  {/if}
                </tr>
              {/each}
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- Right Col: Aggregated Data -->
    <div class="lg:col-span-5 flex flex-col gap-4">
      <div class="flex items-center justify-between">
        <h3 class="text-lg font-bold text-white flex items-center gap-2">
          <span class="material-symbols-outlined text-primary">analytics</span>
          Group Insights
        </h3>
        <span class="badge badge-ghost text-xs">LIVE UPDATES</span>
      </div>

      <!-- Aggregated Preferences -->
      <AggregatedPreferences aggregated={data.aggregated} />
    </div>
  </div>
</div>

<!-- Delete Trip Modal -->
<DeleteTripModal
  bind:open={showDeleteModal}
  tripName={data.trip.name}
  tripId={data.trip.id}
/>

<!-- Leave Trip Modal -->
<LeaveTripModal
  bind:open={showLeaveModal}
  tripName={data.trip.name}
  tripId={data.trip.id}
/>

<!-- Recommendation Warning Modal -->
{#if showRecommendationWarningModal}
  <div class="modal modal-open">
    <div class="modal-box max-w-2xl">
      <h3 class="font-bold text-lg flex items-center gap-2">
        <span class="material-symbols-outlined text-warning">warning</span>
        Proceed with Caution
      </h3>
      <div class="py-4 space-y-4">
        <p class="text-base-content/80">
          We detected some issues that may affect the quality of AI recommendations:
        </p>
        <ul class="list-disc list-inside space-y-2 text-sm">
          {#if data.responseCount < 2}
            <li class="text-warning">
              <strong>Few Responses:</strong> Only {data.responseCount} member{data.responseCount === 1 ? ' has' : 's have'} submitted preferences. More responses will help the AI generate better recommendations.
            </li>
          {/if}
          {#if data.aggregated?.conflicts?.noDateOverlap}
            <li class="text-error">
              <strong>Date Conflict:</strong> {data.aggregated.conflicts.details?.find(d => d.includes('date')) || 'No overlapping dates between all members'}. The AI may struggle to find suitable options.
            </li>
          {/if}
          {#if data.aggregated?.conflicts?.noBudgetOverlap}
            <li class="text-error">
              <strong>Budget Conflict:</strong> {data.aggregated.conflicts.details?.find(d => d.includes('budget') || d.includes('Budget')) || 'Budget ranges don\'t overlap'}. This significantly limits destination options.
            </li>
          {/if}
        </ul>
        <p class="text-base-content/60 text-sm">
          You can still proceed, but consider collecting more responses or asking members to adjust their preferences for better results.
        </p>
      </div>
      <div class="modal-action">
        <button
          class="btn btn-ghost"
          onclick={() => showRecommendationWarningModal = false}
        >
          Cancel
        </button>
        <button
          class="btn btn-primary"
          onclick={() => generateRecommendations()}
          disabled={generatingRecommendations}
        >
          {#if generatingRecommendations}
            <span class="loading loading-spinner loading-sm"></span>
            Generating...
          {:else}
            Proceed Anyway
          {/if}
        </button>
      </div>
    </div>
    <button
      class="modal-backdrop"
      onclick={() => showRecommendationWarningModal = false}
      aria-label="Close modal"
    ></button>
  </div>
{/if}
