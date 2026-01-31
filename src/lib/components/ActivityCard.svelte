<script lang="ts">
  import type { Activity } from "$lib/types";

  // Props
  export let activity: Activity;

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

      <!-- Cost Badge -->
      <div class="badge badge-primary badge-lg flex-shrink-0">
        {formatCost(activity.estimated_cost)}
      </div>
    </div>
  </div>
</div>
