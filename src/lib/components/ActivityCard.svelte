<script lang="ts">
  import type { Activity } from "$lib/types";

  // Props
  export let activity: Activity;
  export let dayIndex: number | undefined = undefined;
  export let activityIndex: number | undefined = undefined;
  export let isFinalized: boolean = false;
  export let onFeedback: ((dayIndex: number, activityIndex: number, activityName: string) => void) | undefined = undefined;
  export let feedbackCount: number | undefined = undefined;

  // Format cost as USD
  function formatCost(amount: number | undefined): string {
    if (amount === undefined || amount === null) return "$0";
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(amount);
  }

  // Handle feedback button click
  function handleFeedbackClick() {
    if (onFeedback && dayIndex !== undefined && activityIndex !== undefined) {
      onFeedback(dayIndex, activityIndex, activity.name);
    }
  }

  // Show feedback button if not finalized and callback is provided
  const showFeedbackButton = !isFinalized && onFeedback !== undefined && dayIndex !== undefined && activityIndex !== undefined;
</script>

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
        <div class="flex items-center gap-4 mt-3 text-sm flex-wrap">
          <!-- Location -->
          <span class="flex items-center gap-1">
            <span
              class="material-symbols-outlined text-xs text-primary"
            >
              location_on
            </span>
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

          <!-- Duration -->
          <span class="flex items-center gap-1">
            <span
              class="material-symbols-outlined text-xs text-base-content/60"
            >
              schedule
            </span>
            {activity.duration_hours}h
          </span>

          <!-- Category -->
          {#if activity.category}
            <span class="badge badge-xs badge-outline capitalize">
              {activity.category}
            </span>
          {/if}
        </div>

        <!-- Tips -->
        {#if activity.tips}
          <div
            class="alert alert-info bg-info/10 border-info/20 mt-3 py-2"
          >
            <span class="material-symbols-outlined text-sm">
              lightbulb
            </span>
            <span class="text-xs">{activity.tips}</span>
          </div>
        {/if}
      </div>

      <!-- Right Side: Cost Badge and Feedback Button -->
      <div class="flex flex-col items-end gap-2 flex-shrink-0">
        <!-- Cost Badge -->
        <div class="badge badge-primary badge-lg">
          {formatCost(activity.estimated_cost)}
        </div>

        <!-- Feedback Button (show if not finalized and callback provided) -->
        {#if showFeedbackButton}
          <button
            type="button"
            class="btn btn-sm btn-ghost gap-1 text-error hover:bg-error/10"
            onclick={handleFeedbackClick}
            title="Report issue with this activity"
          >
            <span class="material-symbols-outlined text-base">thumb_down</span>
            <span class="text-xs">Feedback</span>
          </button>
        {/if}

        <!-- Feedback Count (show for organizers) -->
        {#if feedbackCount !== undefined && feedbackCount > 0}
          <div class="badge badge-error badge-sm gap-1">
            <span class="material-symbols-outlined text-xs">flag</span>
            {feedbackCount}
          </div>
        {/if}
      </div>
    </div>
  </div>
</div>
