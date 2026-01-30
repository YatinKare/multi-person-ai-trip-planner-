<script lang="ts">
  import { onMount, setContext } from "svelte"
  import { writable } from "svelte/store"
  import type { PageData } from "./$types"

  interface Props {
    data: PageData
  }

  let { data }: Props = $props()

  const adminSectionStore = writable("trips")
  setContext("adminSection", adminSectionStore)

  // Get badge class based on trip status
  function getStatusBadgeClass(status: string): string {
    const badges: Record<string, string> = {
      collecting: "badge-warning",
      recommending: "badge-info",
      voting: "badge-info",
      planning: "badge-info",
      finalized: "badge-success"
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

    if (diffMins < 1) return "just now"
    if (diffMins < 60) return `${diffMins}m ago`
    if (diffHours < 24) return `${diffHours}h ago`
    if (diffDays < 7) return `${diffDays}d ago`
    return new Date(dateString).toLocaleDateString()
  }

  // Copy invite link to clipboard
  async function copyInviteLink() {
    const inviteUrl = `${window.location.origin}/join/${data.trip.invite_code}`
    try {
      await navigator.clipboard.writeText(inviteUrl)
      showCopySuccess = true
      setTimeout(() => showCopySuccess = false, 2000)
    } catch (err) {
      console.error("Failed to copy:", err)
    }
  }

  let showCopySuccess = $state(false)
  let isOrganizer = $derived(data.userRole === "organizer")
</script>

<svelte:head>
  <title>{data.trip.name} - TripSync</title>
</svelte:head>

<div class="max-w-7xl mx-auto">
  <!-- Breadcrumbs -->
  <nav class="mb-4 flex items-center text-sm font-medium">
    <a class="text-base-content/60 hover:text-primary transition-colors" href="/trips">All Trips</a>
    <span class="mx-2 text-base-content/40">/</span>
    <span class="text-base-content font-bold">{data.trip.name}</span>
  </nav>

  <!-- Heading Section -->
  <div class="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-8">
    <div class="flex flex-col gap-2">
      <h1 class="text-4xl md:text-5xl font-black text-white tracking-tight">{data.trip.name}</h1>
      <div class="flex items-center gap-3 mt-1">
        <span class="{getStatusBadgeClass(data.trip.status)} gap-2 p-3 font-bold bg-warning/10 border-warning/20 text-warning">
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
        <button class="btn btn-neutral flex items-center gap-2">
          <span class="material-symbols-outlined">edit</span>
          Edit Trip
        </button>
        <button
          class="btn btn-primary flex items-center gap-2 text-base-300 font-bold hover:shadow-[0_0_20px_rgba(19,236,182,0.3)]"
        >
          <span class="material-symbols-outlined">auto_awesome</span>
          Generate Recommendations
        </button>
      {/if}
    </div>
  </div>

  <!-- Invite Action Card -->
  {#if isOrganizer}
    <div class="relative overflow-hidden rounded-2xl bg-base-200 border border-base-300 mb-8">
      <div class="absolute inset-0 z-0 opacity-40 mix-blend-overlay bg-cover bg-center"></div>
      <div class="absolute inset-0 z-0 bg-gradient-to-r from-base-200 via-base-200/95 to-transparent"></div>
      <div class="relative z-10 flex flex-col md:flex-row items-center justify-between p-6 md:p-8 gap-6">
        <div class="flex flex-col gap-2 max-w-xl">
          <div class="flex items-center gap-2 text-primary mb-1">
            <span class="material-symbols-outlined">mail</span>
            <span class="text-sm font-bold uppercase tracking-wider">Invite Friends</span>
          </div>
          <h2 class="text-2xl font-bold text-white">Get the gang together</h2>
          <p class="text-base-content/80">
            Share this unique link with your group to collect their preferences, budget, and availability automatically.
          </p>
        </div>
        <div class="w-full md:max-w-md bg-base-100/50 p-1.5 rounded-xl border border-base-300 flex items-center backdrop-blur-sm">
          <div class="flex-1 px-3 py-2 text-base-content/80 font-mono text-sm truncate select-all">
            {window.location.origin}/join/{data.trip.invite_code}
          </div>
          <button class="btn btn-primary btn-sm h-10 px-4 text-base-300 font-bold gap-2" onclick={copyInviteLink}>
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
      <div class="bg-base-200 rounded-xl border border-base-300 overflow-hidden">
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
                          <div class="w-10 rounded-full {member.role === 'organizer' ? 'ring-2 ring-primary/20' : ''}">
                            <img src={member.profile.avatar_url} alt={member.profile.full_name || "User"} />
                          </div>
                        </div>
                      {:else}
                        <div class="avatar placeholder">
                          <div class="bg-neutral text-neutral-content rounded-full w-10">
                            <span class="text-xs">
                              {member.profile?.full_name?.split(" ").map((n: string) => n[0]).join("").slice(0, 2) || "??"}
                            </span>
                          </div>
                        </div>
                      {/if}
                      <div>
                        <div class="font-bold">
                          {member.profile?.full_name || "Unknown"}
                          {#if member.user_id === data.userId}
                            <span class="text-xs text-base-content/60">(You)</span>
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
                        <span class="material-symbols-outlined text-[14px]">check_circle</span>
                        Responded
                      </div>
                    {:else}
                      <div class="badge badge-warning badge-outline gap-1">
                        <span class="material-symbols-outlined text-[14px]">hourglass_empty</span>
                        Pending
                      </div>
                    {/if}
                  </td>
                  {#if isOrganizer}
                    <td class="text-right">
                      {#if !member.has_responded && member.user_id !== data.userId}
                        <button class="btn btn-xs btn-neutral gap-1">
                          <span class="material-symbols-outlined text-[14px]">notifications_active</span>
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

      <!-- Placeholder for aggregated preferences -->
      <div class="card bg-base-200 border border-base-300 shadow-sm">
        <div class="card-body p-5 gap-4">
          <div class="flex items-center justify-center min-h-[200px] text-center">
            <div>
              <span class="material-symbols-outlined text-6xl text-base-content/20">analytics</span>
              <p class="mt-4 text-base-content/60">
                {#if data.responseCount === 0}
                  Waiting for responses to show insights
                {:else}
                  Insights will appear here once implemented
                {/if}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>

<style>
  /* Import Material Symbols font */
  @import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200');

  .material-symbols-outlined {
    font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
  }
</style>
