<script lang="ts">
  import type { PageData, ActionData } from "./$types"
  import type { Activity, DayItinerary } from "$lib/types"
  import ActivityCard from "$lib/components/ActivityCard.svelte"
  import SuggestActivityModal from "$lib/components/SuggestActivityModal.svelte"
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

  // Feedback modal state
  let showFeedbackModal = $state(false)
  let feedbackActivity = $state<{
    dayIndex: number
    activityIndex: number
    activityName: string
  } | null>(null)
  let feedbackReason = $state("")

  function openFeedbackModal(
    dayIndex: number,
    activityIndex: number,
    activityName: string
  ) {
    feedbackActivity = { dayIndex, activityIndex, activityName }

    // Check if user already has feedback for this activity
    const existingFeedback = data.userFeedback.find(
      (f) =>
        f.day_index === dayIndex &&
        f.activity_index === activityIndex
    )

    feedbackReason = existingFeedback?.reason || ""
    showFeedbackModal = true
  }

  function closeFeedbackModal() {
    showFeedbackModal = false
    feedbackActivity = null
    feedbackReason = ""
  }

  // Check if user has already submitted feedback for an activity
  function hasUserFeedback(dayIndex: number, activityIndex: number): boolean {
    return data.userFeedback.some(
      (f) =>
        f.day_index === dayIndex &&
        f.activity_index === activityIndex
    )
  }

  // Get feedback count for an activity (for organizers)
  function getFeedbackCount(dayIndex: number, activityIndex: number): number {
    return data.feedback.filter(
      (f) =>
        f.day_index === dayIndex &&
        f.activity_index === activityIndex
    ).length
  }

  // Suggest Activity modal state
  let showSuggestModal = $state(false)

  function openSuggestModal() {
    showSuggestModal = true
  }

  function closeSuggestModal() {
    showSuggestModal = false
  }

  // Regeneration modal state
  let showRegenerateModal = $state(false)
  let regenerationFeedback = $state("")
  let isRegenerating = $state(false)

  function openRegenerateModal() {
    showRegenerateModal = true
  }

  function closeRegenerateModal() {
    showRegenerateModal = false
    regenerationFeedback = ""
  }

  // Get regeneration count from itinerary
  const regenerationCount = (data.itinerary as any)?.regeneration_count || 0
  const maxRegenerations = 5
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
      {#if !isFinalized}
        <button
          class="btn btn-primary flex items-center gap-2 font-bold"
          onclick={openSuggestModal}
        >
          <span class="material-symbols-outlined">add_circle</span>
          Suggest Activity
        </button>
      {/if}
      {#if isOrganizer && !isFinalized}
        <button
          class="btn btn-accent flex items-center gap-2 font-bold"
          onclick={openRegenerateModal}
          disabled={regenerationCount >= maxRegenerations}
          title={regenerationCount >= maxRegenerations ? "Maximum regenerations reached" : "Regenerate itinerary with feedback"}
        >
          <span class="material-symbols-outlined">refresh</span>
          Regenerate
        </button>
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

  <!-- Regeneration info (if applicable) -->
  {#if regenerationCount > 0}
    <div class="alert bg-accent/10 border-accent/20 mb-8">
      <span class="material-symbols-outlined text-accent">refresh</span>
      <div class="flex-1">
        <p class="text-base-content/90">
          This itinerary has been regenerated {regenerationCount} {regenerationCount === 1 ? "time" : "times"} based on your feedback.
          {#if regenerationCount >= maxRegenerations}
            <span class="font-bold text-warning">Maximum regenerations reached.</span>
          {:else}
            You can regenerate {maxRegenerations - regenerationCount} more {maxRegenerations - regenerationCount === 1 ? "time" : "times"}.
          {/if}
        </p>
      </div>
    </div>
  {/if}

  <!-- Activity Suggestions (Organizer View) -->
  {#if isOrganizer && data.suggestions.length > 0}
    {@const pendingSuggestions = data.suggestions.filter((s) => s.status === "pending")}
    {#if pendingSuggestions.length > 0}
      <div class="card bg-base-200 border border-primary mb-8">
        <div class="card-body">
          <h3 class="text-xl font-bold text-white flex items-center gap-2 mb-4">
            <span class="material-symbols-outlined text-primary">notifications_active</span>
            Activity Suggestions ({pendingSuggestions.length} pending)
          </h3>
          <p class="text-base-content/70 mb-4">
            Members have suggested the following activities. Review and accept or reject them.
          </p>
          <div class="space-y-3">
            {#each pendingSuggestions as suggestion}
              <div class="card bg-base-300 border border-base-content/10">
                <div class="card-body p-4">
                  <div class="flex flex-col md:flex-row md:items-start justify-between gap-4">
                    <div class="flex-1">
                      <div class="flex items-center gap-2 mb-2">
                        <span class="badge badge-primary">
                          Day {suggestion.day_index + 1} - {suggestion.time_slot.charAt(0).toUpperCase() + suggestion.time_slot.slice(1)}
                        </span>
                        <span class="text-sm text-base-content/60">
                          by {suggestion.user_name}
                        </span>
                      </div>
                      <h4 class="font-bold text-lg text-white mb-2">
                        {suggestion.activity_name}
                      </h4>
                      {#if suggestion.activity_description}
                        <p class="text-base-content/80 text-sm mb-2">
                          {suggestion.activity_description}
                        </p>
                      {/if}
                      <div class="flex flex-wrap gap-3 text-sm">
                        {#if suggestion.location}
                          <span class="flex items-center gap-1 text-base-content/70">
                            <span class="material-symbols-outlined text-xs">location_on</span>
                            {suggestion.location}
                          </span>
                        {/if}
                        {#if suggestion.estimated_cost !== null}
                          <span class="flex items-center gap-1 text-base-content/70">
                            <span class="material-symbols-outlined text-xs">payments</span>
                            ${suggestion.estimated_cost}
                          </span>
                        {/if}
                      </div>
                      {#if suggestion.reason}
                        <div class="mt-3 p-2 bg-base-200 rounded text-sm text-base-content/70">
                          <span class="font-semibold">Why: </span>{suggestion.reason}
                        </div>
                      {/if}
                    </div>
                    <div class="flex gap-2">
                      <form method="POST" action="?/acceptSuggestion" use:enhance>
                        <input type="hidden" name="suggestionId" value={suggestion.id} />
                        <button
                          type="submit"
                          class="btn btn-success btn-sm gap-1"
                          title="Accept suggestion"
                        >
                          <span class="material-symbols-outlined text-sm">check</span>
                          Accept
                        </button>
                      </form>
                      <form method="POST" action="?/rejectSuggestion" use:enhance>
                        <input type="hidden" name="suggestionId" value={suggestion.id} />
                        <button
                          type="submit"
                          class="btn btn-error btn-sm gap-1"
                          title="Reject suggestion"
                        >
                          <span class="material-symbols-outlined text-sm">close</span>
                          Reject
                        </button>
                      </form>
                    </div>
                  </div>
                </div>
              </div>
            {/each}
          </div>
        </div>
      </div>
    {/if}
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
                  {#each morning as activity, activityIndex}
                    <ActivityCard
                      {activity}
                      dayIndex={day.day_number - 1}
                      {activityIndex}
                      {isFinalized}
                      onFeedback={openFeedbackModal}
                      feedbackCount={isOrganizer
                        ? getFeedbackCount(day.day_number - 1, activityIndex)
                        : undefined}
                    />
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
                  {#each afternoon as activity, activityIndex}
                    {@const actualIndex = morning.length + activityIndex}
                    <ActivityCard
                      {activity}
                      dayIndex={day.day_number - 1}
                      activityIndex={actualIndex}
                      {isFinalized}
                      onFeedback={openFeedbackModal}
                      feedbackCount={isOrganizer
                        ? getFeedbackCount(day.day_number - 1, actualIndex)
                        : undefined}
                    />
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
                  {#each evening as activity, activityIndex}
                    {@const actualIndex = morning.length + afternoon.length + activityIndex}
                    <ActivityCard
                      {activity}
                      dayIndex={day.day_number - 1}
                      activityIndex={actualIndex}
                      {isFinalized}
                      onFeedback={openFeedbackModal}
                      feedbackCount={isOrganizer
                        ? getFeedbackCount(day.day_number - 1, actualIndex)
                        : undefined}
                    />
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

        {#if form && "error" in form}
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
            if (!form || !("error" in form)) {
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

<!-- Feedback Modal -->
{#if showFeedbackModal && feedbackActivity}
  <div class="modal modal-open">
    <div class="modal-box max-w-lg">
      <h3 class="font-bold text-2xl mb-4 flex items-center gap-2">
        <span class="material-symbols-outlined text-error">thumb_down</span>
        Activity Feedback
      </h3>

      <div class="space-y-4">
        <p class="text-base-content/80">
          Tell us what you don't like about this activity:
        </p>
        <div class="alert bg-base-300">
          <span class="material-symbols-outlined text-primary">info</span>
          <span class="font-bold">{feedbackActivity.activityName}</span>
        </div>

        {#if form && "error" in form && form.action === "submitFeedback"}
          <div class="alert alert-error">
            <span class="material-symbols-outlined">error</span>
            <span>{form.error}</span>
          </div>
        {/if}

        {#if form && "success" in form && form.action === "submitFeedback"}
          <div class="alert alert-success">
            <span class="material-symbols-outlined">check_circle</span>
            <span>Feedback submitted successfully!</span>
          </div>
        {/if}
      </div>

      <form
        method="POST"
        action="?/submitFeedback"
        use:enhance={() => {
          isSubmitting = true
          return async ({ update }) => {
            await update()
            isSubmitting = false
            if (form && "success" in form && form.action === "submitFeedback") {
              // Close modal after successful submission
              setTimeout(() => {
                closeFeedbackModal()
                window.location.reload()
              }, 1000)
            }
          }
        }}
      >
        <input
          type="hidden"
          name="itinerary_id"
          value={data.itinerary.id}
        />
        <input
          type="hidden"
          name="day_index"
          value={feedbackActivity.dayIndex}
        />
        <input
          type="hidden"
          name="activity_index"
          value={feedbackActivity.activityIndex}
        />
        <input
          type="hidden"
          name="activity_name"
          value={feedbackActivity.activityName}
        />

        <div class="form-control mt-4">
          <label class="label" for="reason">
            <span class="label-text">Reason (Optional)</span>
          </label>
          <textarea
            id="reason"
            name="reason"
            class="textarea textarea-bordered h-24"
            placeholder="e.g., Too expensive, not interested in this type of activity, accessibility concerns..."
            bind:value={feedbackReason}
          ></textarea>
        </div>

        <div class="modal-action">
          <button
            type="button"
            class="btn btn-ghost"
            onclick={closeFeedbackModal}
            disabled={isSubmitting}
          >
            Cancel
          </button>
          <button
            type="submit"
            class="btn btn-error gap-2"
            disabled={isSubmitting}
          >
            {#if isSubmitting}
              <span class="loading loading-spinner loading-sm"></span>
              Submitting...
            {:else}
              <span class="material-symbols-outlined">thumb_down</span>
              Submit Feedback
            {/if}
          </button>
        </div>
      </form>
    </div>
    <button
      type="button"
      class="modal-backdrop"
      onclick={closeFeedbackModal}
      aria-label="Close modal"
    ></button>
  </div>
{/if}

<!-- Suggest Activity Modal -->
<SuggestActivityModal
  show={showSuggestModal}
  tripId={data.trip.id}
  totalDays={tripLengthDays}
  onClose={closeSuggestModal}
  actionData={form}
/>

<!-- Regenerate Itinerary Modal -->
{#if showRegenerateModal}
  <div class="modal modal-open">
    <div class="modal-box max-w-2xl">
      <h3 class="font-bold text-2xl mb-4 flex items-center gap-2">
        <span class="material-symbols-outlined text-accent">refresh</span>
        Regenerate Itinerary
      </h3>

      <div class="space-y-4">
        <p class="text-base-content/80">
          Provide feedback on what you'd like to change about the current itinerary. The AI will use your feedback to generate an improved version.
        </p>

        <div class="alert bg-base-300">
          <span class="material-symbols-outlined text-info">lightbulb</span>
          <div class="flex-1 text-sm">
            <p class="font-semibold mb-1">Feedback examples:</p>
            <ul class="list-disc list-inside space-y-1 text-base-content/70">
              <li>"Add more outdoor activities"</li>
              <li>"Replace expensive restaurants with more budget-friendly options"</li>
              <li>"Include more cultural experiences and museums"</li>
              <li>"Reduce the pace - add more relaxation time"</li>
            </ul>
          </div>
        </div>

        {#if regenerationCount >= maxRegenerations - 1 && regenerationCount < maxRegenerations}
          <div class="alert alert-warning">
            <span class="material-symbols-outlined">warning</span>
            <span>This is your last regeneration. Make sure your feedback is clear!</span>
          </div>
        {/if}

        {#if form && "error" in form && form.action === "regenerate"}
          <div class="alert alert-error">
            <span class="material-symbols-outlined">error</span>
            <span>{form.error}</span>
          </div>
        {/if}

        {#if form && "success" in form && form.action === "regenerate"}
          <div class="alert alert-success">
            <span class="material-symbols-outlined">check_circle</span>
            <span>Itinerary regenerated successfully!</span>
          </div>
        {/if}
      </div>

      <form
        method="POST"
        action="?/regenerate"
        use:enhance={() => {
          isRegenerating = true
          return async ({ update }) => {
            await update()
            isRegenerating = false
            if (form && "success" in form && form.action === "regenerate") {
              // Close modal and reload page after successful regeneration
              setTimeout(() => {
                closeRegenerateModal()
                window.location.reload()
              }, 1500)
            }
          }
        }}
      >
        <input type="hidden" name="regeneration_count" value={regenerationCount} />

        <div class="form-control mt-4">
          <label class="label" for="feedback">
            <span class="label-text font-semibold">Your Feedback <span class="text-error">*</span></span>
            <span class="label-text-alt">{regenerationFeedback.length}/1000</span>
          </label>
          <textarea
            id="feedback"
            name="feedback"
            class="textarea textarea-bordered h-32"
            placeholder="Describe what you'd like to change about the itinerary..."
            bind:value={regenerationFeedback}
            maxlength="1000"
            required
          ></textarea>
          <label class="label">
            <span class="label-text-alt text-base-content/60">
              Be specific about what you want changed (min 10 characters)
            </span>
          </label>
        </div>

        <div class="modal-action">
          <button
            type="button"
            class="btn btn-ghost"
            onclick={closeRegenerateModal}
            disabled={isRegenerating}
          >
            Cancel
          </button>
          <button
            type="submit"
            class="btn btn-accent gap-2"
            disabled={isRegenerating || regenerationFeedback.length < 10}
          >
            {#if isRegenerating}
              <span class="loading loading-spinner loading-sm"></span>
              Regenerating...
            {:else}
              <span class="material-symbols-outlined">refresh</span>
              Regenerate Itinerary
            {/if}
          </button>
        </div>
      </form>
    </div>
    <button
      type="button"
      class="modal-backdrop"
      onclick={closeRegenerateModal}
      aria-label="Close modal"
    ></button>
  </div>
{/if}
