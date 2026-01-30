<script lang="ts">
  import DeleteTripModal from "$lib/components/DeleteTripModal.svelte"
  import LeaveTripModal from "$lib/components/LeaveTripModal.svelte"
  import AggregatedPreferences from "$lib/components/AggregatedPreferences.svelte"
  import { page } from "$app/state"
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

  // Generate recommendations via FastAPI backend
  async function generateRecommendations() {
    if (!canGenerateRecommendations || generatingRecommendations) return

    generatingRecommendations = true

    try {
      // Get the Supabase session token
      const {
        data: { session },
      } = await data.supabase.auth.getSession()

      if (!session) {
        alert("Session expired. Please refresh the page.")
        return
      }

      // Call FastAPI backend
      const response = await fetch(
        `http://localhost:8000/api/trips/${data.trip.id}/recommendations`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${session.access_token}`,
          },
        },
      )

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || "Failed to generate recommendations")
      }

      await response.json()

      // Redirect to recommendations page
      window.location.href = `/trips/${data.trip.id}/recommendations`
    } catch (err) {
      console.error("Error generating recommendations:", err)
      alert(
        err instanceof Error
          ? err.message
          : "Failed to generate recommendations. Please try again.",
      )
    } finally {
      generatingRecommendations = false
    }
  }

  let showCopySuccess = $state(false)
  let showDeleteModal = $state(false)
  let showLeaveModal = $state(false)
  let isOrganizer = $derived(data.userRole === "organizer")
  let generatingRecommendations = $state(false)

  // Can generate recommendations if:
  // 1. User is organizer
  // 2. At least 1 member has submitted preferences
  // 3. Recommendations haven't been generated yet
  let canGenerateRecommendations = $derived(
    isOrganizer && data.responseCount > 0 && !data.hasRecommendations,
  )
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
            onclick={() => generateRecommendations()}
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
                        <button class="btn btn-xs btn-neutral gap-1">
                          <span class="material-symbols-outlined text-[14px]"
                            >notifications_active</span
                          >
                          Nudge
                        </button>
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
