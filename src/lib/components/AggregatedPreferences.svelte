<script lang="ts">
  import type { AggregatedPreferences } from "$lib/server/aggregatePreferences"

  interface Props {
    aggregated: AggregatedPreferences | null
  }

  let { aggregated }: Props = $props()

  function formatDate(dateStr: string | null): string {
    if (!dateStr) return "N/A"
    return new Date(dateStr).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    })
  }

  function getDurationLabel(duration: string): string {
    const labels: Record<string, string> = {
      "2-3-days": "2-3 days",
      "4-5-days": "4-5 days",
      "1-week": "1 week",
      "1-plus-week": "1+ weeks",
      flexible: "Flexible",
    }
    return labels[duration] || duration
  }

  function getVibeLabel(vibe: string): string {
    const labels: Record<string, string> = {
      beach: "Beach",
      city: "City",
      nature: "Nature",
      adventure: "Adventure",
      relaxation: "Relaxing",
      nightlife: "Party",
      culture: "Culture",
      food: "Foodie",
    }
    return labels[vibe] || vibe
  }

  function getScopeLabel(scope: string): string {
    const labels: Record<string, string> = {
      domestic: "Domestic",
      international: "International",
      either: "Either",
    }
    return labels[scope] || scope
  }
</script>

{#if !aggregated}
  <div class="card bg-base-200 border border-base-300 shadow-sm">
    <div class="card-body p-5 gap-4">
      <div class="flex items-center justify-center min-h-[200px] text-center">
        <div>
          <span class="material-symbols-outlined text-6xl text-base-content/20"
            >analytics</span
          >
          <p class="mt-4 text-base-content/60">
            Waiting for responses to show insights
          </p>
        </div>
      </div>
    </div>
  </div>
{:else}
  <!-- Conflicts Alert (if any) -->
  {#if aggregated.conflicts.hasConflicts}
    <div class="alert alert-warning shadow-sm mb-4">
      <span class="material-symbols-outlined">warning</span>
      <div class="flex flex-col gap-1">
        <span class="font-bold">Conflicts Detected</span>
        <ul class="text-sm list-disc list-inside">
          {#each aggregated.conflicts.details as conflict}
            <li>{conflict}</li>
          {/each}
        </ul>
      </div>
    </div>
  {/if}

  <!-- Date Overlap -->
  <div class="card bg-base-200 border border-base-300 shadow-sm">
    <div class="card-body p-5 gap-4">
      <div class="flex items-center gap-2">
        <span class="material-symbols-outlined text-primary"
          >calendar_month</span
        >
        <h4 class="font-bold text-white">Date Window</h4>
      </div>

      {#if aggregated.dates.commonWindow}
        <div class="bg-base-100 rounded-lg p-4 border border-primary/20">
          <div class="flex items-center justify-between mb-2">
            <span class="text-sm text-base-content/60">Common Availability</span
            >
            <span class="badge badge-primary badge-sm">Overlap Found</span>
          </div>
          <div class="text-lg font-bold text-white">
            {formatDate(aggregated.dates.commonWindow.start)} - {formatDate(
              aggregated.dates.commonWindow.end,
            )}
          </div>
        </div>
      {:else if aggregated.dates.earliestCommonStart && aggregated.dates.latestCommonEnd}
        <div class="bg-base-100 rounded-lg p-4 border border-warning/20">
          <div class="flex items-center gap-2 mb-2">
            <span class="material-symbols-outlined text-warning text-sm"
              >warning</span
            >
            <span class="text-sm text-warning font-medium"
              >No overlap between all members</span
            >
          </div>
          <div class="text-sm text-base-content/60">
            Latest start: {formatDate(aggregated.dates.earliestCommonStart)}<br
            />
            Earliest end: {formatDate(aggregated.dates.latestCommonEnd)}
          </div>
        </div>
      {:else}
        <p class="text-base-content/60 text-sm">
          No date preferences submitted yet
        </p>
      {/if}

      {#if aggregated.dates.idealDurations.length > 0}
        <div class="flex flex-wrap gap-2 mt-2">
          <span class="text-xs text-base-content/60">Preferred durations:</span>
          {#each aggregated.dates.idealDurations as duration}
            <span class="badge badge-outline badge-sm"
              >{getDurationLabel(duration)}</span
            >
          {/each}
        </div>
      {/if}
    </div>
  </div>

  <!-- Budget Range -->
  <div class="card bg-base-200 border border-base-300 shadow-sm">
    <div class="card-body p-5 gap-4">
      <div class="flex items-center gap-2">
        <span class="material-symbols-outlined text-primary">payments</span>
        <h4 class="font-bold text-white">Budget Range</h4>
      </div>

      {#if aggregated.budget.minBudget > 0 || aggregated.budget.maxBudget > 0}
        <div class="bg-base-100 rounded-lg p-4">
          <div class="flex items-center justify-between mb-3">
            <div>
              <div class="text-sm text-base-content/60">Min</div>
              <div class="text-2xl font-bold text-white">
                ${aggregated.budget.minBudget}
              </div>
            </div>
            <div class="text-base-content/40">━━━</div>
            <div class="text-right">
              <div class="text-sm text-base-content/60">Max</div>
              <div class="text-2xl font-bold text-white">
                ${aggregated.budget.maxBudget >= 5000
                  ? aggregated.budget.maxBudget + "+"
                  : aggregated.budget.maxBudget}
              </div>
            </div>
          </div>

          {#if aggregated.budget.commonInclusions.length > 0}
            <div class="flex flex-wrap gap-2 pt-3 border-t border-base-300">
              <span class="text-xs text-base-content/60">Included by all:</span>
              {#each aggregated.budget.commonInclusions as inclusion}
                <span class="badge badge-primary badge-sm">{inclusion}</span>
              {/each}
            </div>
          {/if}
        </div>
      {:else}
        <p class="text-base-content/60 text-sm">
          No budget preferences submitted yet
        </p>
      {/if}
    </div>
  </div>

  <!-- Vibes -->
  <div class="card bg-base-200 border border-base-300 shadow-sm">
    <div class="card-body p-5 gap-4">
      <div class="flex items-center gap-2">
        <span class="material-symbols-outlined text-primary">explore</span>
        <h4 class="font-bold text-white">Destination Vibes</h4>
      </div>

      {#if aggregated.destination.allVibes.length > 0}
        <div>
          {#if aggregated.destination.commonVibes.length > 0}
            <div class="mb-3">
              <span
                class="text-xs text-base-content/60 uppercase tracking-wider font-bold mb-2 block"
                >Common to All</span
              >
              <div class="flex flex-wrap gap-2">
                {#each aggregated.destination.commonVibes as vibe}
                  <span class="badge badge-primary gap-1">
                    <span class="material-symbols-outlined text-xs"
                      >check_circle</span
                    >
                    {getVibeLabel(vibe)}
                  </span>
                {/each}
              </div>
            </div>
          {:else if !aggregated.conflicts.noCommonVibes}
            <div class="alert alert-info text-sm mb-3">
              <span class="material-symbols-outlined">info</span>
              <span
                >No vibes selected by all members, but some overlap exists</span
              >
            </div>
          {/if}

          <div>
            <span
              class="text-xs text-base-content/60 uppercase tracking-wider font-bold mb-2 block"
              >All Selected</span
            >
            <div class="flex flex-wrap gap-2">
              {#each aggregated.destination.allVibes as vibe}
                <span class="badge badge-outline badge-sm"
                  >{getVibeLabel(vibe)}</span
                >
              {/each}
            </div>
          </div>
        </div>

        {#if Object.keys(aggregated.destination.popularScopes).length > 0}
          <div class="flex flex-wrap gap-2 pt-3 border-t border-base-300">
            <span class="text-xs text-base-content/60">Travel scope:</span>
            {#each Object.entries(aggregated.destination.popularScopes) as [scope, count]}
              <span class="badge badge-ghost badge-sm"
                >{getScopeLabel(scope)} ({count})</span
              >
            {/each}
          </div>
        {/if}
      {:else}
        <p class="text-base-content/60 text-sm">
          No destination preferences submitted yet
        </p>
      {/if}
    </div>
  </div>

  <!-- Constraints -->
  <div class="card bg-base-200 border border-base-300 shadow-sm">
    <div class="card-body p-5 gap-4">
      <div class="flex items-center gap-2">
        <span class="material-symbols-outlined text-primary">shield</span>
        <h4 class="font-bold text-white">Requirements & Constraints</h4>
      </div>

      {#if aggregated.constraints.dietary.length > 0}
        <div>
          <span
            class="text-xs text-base-content/60 uppercase tracking-wider font-bold mb-2 block"
            >Dietary</span
          >
          <div class="flex flex-wrap gap-2">
            {#each aggregated.constraints.dietary as diet}
              <span class="badge badge-warning badge-outline badge-sm"
                >{diet}</span
              >
            {/each}
          </div>
        </div>
      {/if}

      {#if aggregated.constraints.accessibility.length > 0}
        <div>
          <span
            class="text-xs text-base-content/60 uppercase tracking-wider font-bold mb-2 block"
            >Accessibility</span
          >
          <div class="flex flex-wrap gap-2">
            {#each aggregated.constraints.accessibility as access}
              <span class="badge badge-info badge-outline badge-sm"
                >{access}</span
              >
            {/each}
          </div>
        </div>
      {/if}

      {#if aggregated.constraints.hardNos.length > 0}
        <div>
          <span
            class="text-xs text-base-content/60 uppercase tracking-wider font-bold mb-2 block"
            >Deal-breakers</span
          >
          <div class="flex flex-col gap-2">
            {#each aggregated.constraints.hardNos as hardNo}
              <div
                class="text-sm text-base-content/80 bg-base-100 rounded p-2 border-l-2 border-error"
              >
                {hardNo}
              </div>
            {/each}
          </div>
        </div>
      {/if}

      {#if aggregated.constraints.dietary.length === 0 && aggregated.constraints.accessibility.length === 0 && aggregated.constraints.hardNos.length === 0}
        <p class="text-base-content/60 text-sm">
          No special requirements submitted
        </p>
      {/if}
    </div>
  </div>
{/if}

<style>
  .material-symbols-outlined {
    font-variation-settings:
      "FILL" 0,
      "wght" 400,
      "GRAD" 0,
      "opsz" 24;
  }
</style>
