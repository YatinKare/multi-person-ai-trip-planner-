<script lang="ts">
  import { enhance } from "$app/forms"
  import type { PageData } from "./$types"

  interface Props {
    data: PageData
  }

  let { data }: Props = $props()

  interface DatesPref {
    earliestStart?: string
    latestEnd?: string
    idealDuration?: string
    flexible?: boolean
  }

  interface BudgetPref {
    min?: number
    max?: number
    includeFlights?: boolean
    includeAccommodation?: boolean
    includeFood?: boolean
    includeActivities?: boolean
    flexibility?: string
  }

  interface DestinationPref {
    vibes?: string[]
    scope?: string
    specificPlaces?: string
    placesToAvoid?: string
  }

  interface ConstraintsPref {
    dietary?: string[]
    otherDietary?: string
    accessibility?: string[]
    otherAccessibility?: string
    hardNos?: string
  }

  // Form state
  let earliestStartDate = $state("")
  let latestEndDate = $state("")
  let tripDuration = $state("")
  let flexibleDates = $state(false)

  let budgetMin = $state(500)
  let budgetMax = $state(2000)
  let includeFlights = $state(false)
  let includeAccommodation = $state(false)
  let includeFood = $state(false)
  let includeActivities = $state(false)
  let budgetFlexibility = $state("prefer_under")

  let selectedVibes = $state<string[]>([])
  let specificPlaces = $state("")
  let placesToAvoid = $state("")
  let travelScope = $state("either")

  let selectedDietary = $state<string[]>([])
  let otherDietary = $state("")
  let selectedAccessibility = $state<string[]>([])
  let otherAccessibility = $state("")
  let hardNos = $state("")

  let additionalNotes = $state("")

  // Available vibes
  const vibes = [
    { id: "beach", label: "Beach", icon: "beach_access" },
    { id: "city", label: "City", icon: "location_city" },
    { id: "nature", label: "Nature", icon: "landscape" },
    { id: "adventure", label: "Adventure", icon: "hiking" },
    { id: "relaxation", label: "Relaxing", icon: "spa" },
    { id: "nightlife", label: "Party", icon: "nightlife" },
    { id: "culture", label: "Culture", icon: "museum" },
    { id: "food", label: "Foodie", icon: "restaurant" },
  ]

  // Dietary restrictions
  const dietaryOptions = [
    "Vegetarian",
    "Vegan",
    "Gluten-free",
    "Halal",
    "Kosher",
    "Nut Allergy",
    "Other",
  ]

  // Accessibility needs
  const accessibilityOptions = [
    "Wheelchair Accessible",
    "Hearing Accommodations",
    "Visual Accommodations",
    "Mobility Assistance",
    "Other",
  ]

  // Toggle vibe selection
  function toggleVibe(vibeId: string) {
    if (selectedVibes.includes(vibeId)) {
      selectedVibes = selectedVibes.filter((v) => v !== vibeId)
    } else {
      selectedVibes = [...selectedVibes, vibeId]
    }
  }

  // Toggle dietary selection
  function toggleDietary(option: string) {
    if (selectedDietary.includes(option)) {
      selectedDietary = selectedDietary.filter((d) => d !== option)
    } else {
      selectedDietary = [...selectedDietary, option]
    }
  }

  // Toggle accessibility selection
  function toggleAccessibility(option: string) {
    if (selectedAccessibility.includes(option)) {
      selectedAccessibility = selectedAccessibility.filter((a) => a !== option)
    } else {
      selectedAccessibility = [...selectedAccessibility, option]
    }
  }

  // Load existing preferences if they exist
  $effect(() => {
    if (data.existingPreferences) {
      const prefs = data.existingPreferences

      if (
        prefs.dates &&
        typeof prefs.dates === "object" &&
        !Array.isArray(prefs.dates)
      ) {
        const dates = prefs.dates as unknown as DatesPref
        earliestStartDate = dates.earliestStart || ""
        latestEndDate = dates.latestEnd || ""
        tripDuration = dates.idealDuration || ""
        flexibleDates = dates.flexible || false
      }

      if (
        prefs.budget &&
        typeof prefs.budget === "object" &&
        !Array.isArray(prefs.budget)
      ) {
        const budget = prefs.budget as unknown as BudgetPref
        budgetMin = budget.min || 500
        budgetMax = budget.max || 2000
        includeFlights = budget.includeFlights || false
        includeAccommodation = budget.includeAccommodation || false
        includeFood = budget.includeFood || false
        includeActivities = budget.includeActivities || false
        budgetFlexibility = budget.flexibility || "prefer_under"
      }

      if (
        prefs.destination_prefs &&
        typeof prefs.destination_prefs === "object" &&
        !Array.isArray(prefs.destination_prefs)
      ) {
        const destPrefs = prefs.destination_prefs as unknown as DestinationPref
        selectedVibes = destPrefs.vibes || []
        specificPlaces = destPrefs.specificPlaces || ""
        placesToAvoid = destPrefs.placesToAvoid || ""
        travelScope = destPrefs.scope || "either"
      }

      if (
        prefs.constraints &&
        typeof prefs.constraints === "object" &&
        !Array.isArray(prefs.constraints)
      ) {
        const constraints = prefs.constraints as unknown as ConstraintsPref
        selectedDietary = constraints.dietary || []
        otherDietary = constraints.otherDietary || ""
        selectedAccessibility = constraints.accessibility || []
        otherAccessibility = constraints.otherAccessibility || ""
        hardNos = constraints.hardNos || ""
      }

      additionalNotes = prefs.notes || ""
    }
  })

  let submitting = $state(false)
</script>

<svelte:head>
  <title>Preferences - {data.trip.name} - TripSync</title>
</svelte:head>

<div class="max-w-4xl mx-auto">
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
    <span class="text-base-content font-bold">Preferences</span>
  </nav>

  <!-- Header -->
  <div class="flex flex-col gap-4 mb-12">
    <h1 class="text-3xl md:text-5xl font-extrabold text-white tracking-tight">
      Let's plan your perfect trip
    </h1>
    <p class="text-base-content/60 text-lg">
      Tell us what you need, and our AI will sync it with your group.
    </p>
  </div>

  <form
    method="POST"
    action="?/submitPreferences"
    use:enhance={() => {
      submitting = true
      return async ({ update }) => {
        await update()
        submitting = false
      }
    }}
    class="flex flex-col gap-12 pb-32"
  >
    <!-- Section 1: Dates -->
    <section
      class="flex flex-col gap-6 p-6 md:p-8 rounded-2xl bg-base-200 border border-base-300"
    >
      <div class="flex items-center gap-3 mb-2">
        <div
          class="size-8 rounded-full bg-primary/20 flex items-center justify-center text-primary font-bold"
        >
          1
        </div>
        <h2 class="text-xl font-bold text-white">When are you free?</h2>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <label class="form-control w-full">
          <div class="label">
            <span class="label-text font-medium text-white"
              >Earliest Start Date</span
            >
          </div>
          <input
            type="date"
            name="earliestStartDate"
            bind:value={earliestStartDate}
            class="input input-bordered w-full bg-base-100"
            required
          />
        </label>

        <label class="form-control w-full">
          <div class="label">
            <span class="label-text font-medium text-white"
              >Latest End Date</span
            >
          </div>
          <input
            type="date"
            name="latestEndDate"
            bind:value={latestEndDate}
            class="input input-bordered w-full bg-base-100"
            required
          />
        </label>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-6 pt-4">
        <label class="form-control w-full">
          <div class="label">
            <span class="label-text font-medium text-white">Trip Duration</span>
          </div>
          <select
            name="tripDuration"
            bind:value={tripDuration}
            class="select select-bordered w-full bg-base-100"
            required
          >
            <option value="">Select duration</option>
            <option value="2-3-days">Weekend Trip (2-3 days)</option>
            <option value="4-5-days">Long Weekend (4-5 days)</option>
            <option value="1-week">One Week (5-7 days)</option>
            <option value="1-plus-week">More than a Week (7+ days)</option>
            <option value="flexible">Flexible</option>
          </select>
        </label>

        <div
          class="form-control p-4 bg-base-100 border border-base-300 rounded-lg flex-row justify-between items-center"
        >
          <div class="flex flex-col gap-1">
            <span class="font-medium text-white text-sm">Flexible Dates?</span>
            <span class="text-xs text-base-content/60"
              >+/- 3 days from selection</span
            >
          </div>
          <input
            type="checkbox"
            name="flexibleDates"
            bind:checked={flexibleDates}
            class="toggle toggle-primary"
            value="true"
          />
        </div>
      </div>
    </section>

    <!-- Section 2: Budget -->
    <section
      class="flex flex-col gap-6 p-6 md:p-8 rounded-2xl bg-base-200 border border-base-300"
    >
      <div class="flex items-center gap-3 mb-2">
        <div
          class="size-8 rounded-full bg-primary/20 flex items-center justify-center text-primary font-bold"
        >
          2
        </div>
        <h2 class="text-xl font-bold text-white">
          What's your spending range?
        </h2>
      </div>

      <div class="px-2 py-6">
        <div class="flex justify-between mb-4">
          <div class="flex flex-col">
            <span
              class="text-base-content/60 text-xs uppercase tracking-wider font-bold"
              >Min</span
            >
            <span class="text-white text-xl font-bold">${budgetMin}</span>
          </div>
          <div class="flex flex-col text-right">
            <span
              class="text-base-content/60 text-xs uppercase tracking-wider font-bold"
              >Max</span
            >
            <span class="text-white text-xl font-bold"
              >${budgetMax >= 5000 ? budgetMax + "+" : budgetMax}</span
            >
          </div>
        </div>

        <div class="grid grid-cols-2 gap-4 mb-2">
          <div>
            <label class="label" for="text">
              <span class="label-text text-sm">Min Budget</span>
            </label>
            <input
              type="range"
              name="budgetMin"
              bind:value={budgetMin}
              min="0"
              max="5000"
              step="100"
              class="range range-xs range-primary"
            />
          </div>
          <div>
            <label class="label" for="budget-max">
              <span class="label-text text-sm">Max Budget</span>
            </label>
            <input
              id="budget-max"
              type="range"
              name="budgetMax"
              bind:value={budgetMax}
              min="0"
              max="5000"
              step="100"
              class="range range-xs range-primary"
            />
          </div>
        </div>
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <label
          class="label cursor-pointer p-4 bg-base-100 border border-base-300 rounded-lg hover:border-primary/50 transition-colors justify-start gap-3"
        >
          <input
            type="checkbox"
            name="includeFlights"
            bind:checked={includeFlights}
            class="checkbox checkbox-primary checkbox-sm"
            value="true"
          />
          <span class="label-text font-medium text-white">Include Flights</span>
        </label>
        <label
          class="label cursor-pointer p-4 bg-base-100 border border-base-300 rounded-lg hover:border-primary/50 transition-colors justify-start gap-3"
        >
          <input
            type="checkbox"
            name="includeAccommodation"
            bind:checked={includeAccommodation}
            class="checkbox checkbox-primary checkbox-sm"
            value="true"
          />
          <span class="label-text font-medium text-white"
            >Include Accommodation</span
          >
        </label>
        <label
          class="label cursor-pointer p-4 bg-base-100 border border-base-300 rounded-lg hover:border-primary/50 transition-colors justify-start gap-3"
        >
          <input
            type="checkbox"
            name="includeFood"
            bind:checked={includeFood}
            class="checkbox checkbox-primary checkbox-sm"
            value="true"
          />
          <span class="label-text font-medium text-white">Include Food</span>
        </label>
        <label
          class="label cursor-pointer p-4 bg-base-100 border border-base-300 rounded-lg hover:border-primary/50 transition-colors justify-start gap-3"
        >
          <input
            type="checkbox"
            name="includeActivities"
            bind:checked={includeActivities}
            class="checkbox checkbox-primary checkbox-sm"
            value="true"
          />
          <span class="label-text font-medium text-white"
            >Include Activities</span
          >
        </label>
      </div>

      <div class="form-control">
        <div class="label">
          <span class="label-text font-medium text-white"
            >Budget Flexibility</span
          >
        </div>
        <div class="flex flex-col gap-2">
          <label
            class="label cursor-pointer p-3 bg-base-100 border border-base-300 rounded-lg hover:border-primary/50 transition-colors justify-start gap-3"
          >
            <input
              type="radio"
              name="budgetFlexibility"
              value="hard_limit"
              bind:group={budgetFlexibility}
              class="radio radio-primary radio-sm"
            />
            <span class="label-text font-medium text-white"
              >Hard limit - Cannot exceed</span
            >
          </label>
          <label
            class="label cursor-pointer p-3 bg-base-100 border border-base-300 rounded-lg hover:border-primary/50 transition-colors justify-start gap-3"
          >
            <input
              type="radio"
              name="budgetFlexibility"
              value="prefer_under"
              bind:group={budgetFlexibility}
              class="radio radio-primary radio-sm"
            />
            <span class="label-text font-medium text-white"
              >Prefer to stay under</span
            >
          </label>
          <label
            class="label cursor-pointer p-3 bg-base-100 border border-base-300 rounded-lg hover:border-primary/50 transition-colors justify-start gap-3"
          >
            <input
              type="radio"
              name="budgetFlexibility"
              value="no_limit"
              bind:group={budgetFlexibility}
              class="radio radio-primary radio-sm"
            />
            <span class="label-text font-medium text-white"
              >No limit - Just a guideline</span
            >
          </label>
        </div>
      </div>
    </section>

    <!-- Section 3: Destination -->
    <section
      class="flex flex-col gap-6 p-6 md:p-8 rounded-2xl bg-base-200 border border-base-300"
    >
      <div class="flex items-center gap-3 mb-2">
        <div
          class="size-8 rounded-full bg-primary/20 flex items-center justify-center text-primary font-bold"
        >
          3
        </div>
        <h2 class="text-xl font-bold text-white">What's the vibe?</h2>
      </div>

      <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
        {#each vibes as vibe}
          <button
            type="button"
            onclick={() => toggleVibe(vibe.id)}
            class="card bg-base-100 border-2 cursor-pointer hover:bg-base-300 transition-all h-40 items-center justify-center relative {selectedVibes.includes(
              vibe.id,
            )
              ? 'border-primary'
              : 'border-base-300 hover:border-primary/50 hover:-translate-y-1'}"
          >
            <span
              class="material-symbols-outlined text-3xl mb-2 {selectedVibes.includes(
                vibe.id,
              )
                ? 'text-primary'
                : 'text-base-content/60'}">{vibe.icon}</span
            >
            <span
              class="font-bold {selectedVibes.includes(vibe.id)
                ? 'text-white'
                : 'text-base-content/60'}">{vibe.label}</span
            >
            {#if selectedVibes.includes(vibe.id)}
              <div class="absolute top-2 right-2 text-primary">
                <span class="material-symbols-outlined text-xl"
                  >check_circle</span
                >
              </div>
            {/if}
          </button>
        {/each}
      </div>

      <!-- Hidden input to store selected vibes -->
      <input
        type="hidden"
        name="selectedVibes"
        value={JSON.stringify(selectedVibes)}
      />

      <div class="form-control">
        <div class="label">
          <span class="label-text font-medium text-white"
            >Domestic or International?</span
          >
        </div>
        <div class="flex flex-col sm:flex-row gap-2">
          <label
            class="label cursor-pointer p-3 bg-base-100 border border-base-300 rounded-lg hover:border-primary/50 transition-colors justify-start gap-3 flex-1"
          >
            <input
              type="radio"
              name="travelScope"
              value="domestic"
              bind:group={travelScope}
              class="radio radio-primary radio-sm"
            />
            <span class="label-text font-medium text-white">Domestic</span>
          </label>
          <label
            class="label cursor-pointer p-3 bg-base-100 border border-base-300 rounded-lg hover:border-primary/50 transition-colors justify-start gap-3 flex-1"
          >
            <input
              type="radio"
              name="travelScope"
              value="international"
              bind:group={travelScope}
              class="radio radio-primary radio-sm"
            />
            <span class="label-text font-medium text-white">International</span>
          </label>
          <label
            class="label cursor-pointer p-3 bg-base-100 border border-base-300 rounded-lg hover:border-primary/50 transition-colors justify-start gap-3 flex-1"
          >
            <input
              type="radio"
              name="travelScope"
              value="either"
              bind:group={travelScope}
              class="radio radio-primary radio-sm"
            />
            <span class="label-text font-medium text-white">Either</span>
          </label>
        </div>
      </div>

      <div class="form-control">
        <div class="label">
          <span class="label-text font-medium text-white"
            >Specific places or interests?</span
          >
        </div>
        <textarea
          name="specificPlaces"
          bind:value={specificPlaces}
          class="textarea textarea-bordered h-24 bg-base-100"
          placeholder="e.g. Must visit the Louvre, want to try street food, interested in architecture..."
        ></textarea>
      </div>

      <div class="form-control">
        <div class="label">
          <span class="label-text font-medium text-white">Places to avoid?</span
          >
        </div>
        <textarea
          name="placesToAvoid"
          bind:value={placesToAvoid}
          class="textarea textarea-bordered h-20 bg-base-100"
          placeholder="e.g. Tourist traps, crowded beaches, cold destinations..."
        ></textarea>
      </div>
    </section>

    <!-- Section 4: Constraints -->
    <section
      class="flex flex-col gap-6 p-6 md:p-8 rounded-2xl bg-base-200 border border-base-300"
    >
      <div class="flex items-center gap-3 mb-2">
        <div
          class="size-8 rounded-full bg-primary/20 flex items-center justify-center text-primary font-bold"
        >
          4
        </div>
        <h2 class="text-xl font-bold text-white">Any special requirements?</h2>
      </div>

      <div class="form-control">
        <div class="label">
          <span class="label-text font-medium text-white"
            >Dietary Restrictions</span
          >
        </div>
        <div class="flex flex-wrap gap-3">
          {#each dietaryOptions as option}
            <button
              type="button"
              onclick={() => toggleDietary(option)}
              class="btn btn-sm gap-2 rounded-full {selectedDietary.includes(
                option,
              )
                ? 'btn-ghost bg-primary/10 text-primary hover:bg-primary/20 border border-primary'
                : 'btn-outline border-base-300 text-base-content/60 hover:text-white hover:border-primary/50'}"
            >
              {option}
              <span class="material-symbols-outlined text-sm"
                >{selectedDietary.includes(option) ? "close" : "add"}</span
              >
            </button>
          {/each}
        </div>
        {#if selectedDietary.includes("Other")}
          <input
            type="text"
            name="otherDietary"
            bind:value={otherDietary}
            placeholder="Please specify other dietary restrictions"
            class="input input-bordered w-full bg-base-100 mt-3"
          />
        {/if}
      </div>

      <!-- Hidden input to store selected dietary -->
      <input
        type="hidden"
        name="selectedDietary"
        value={JSON.stringify(selectedDietary)}
      />

      <div class="form-control">
        <div class="label">
          <span class="label-text font-medium text-white"
            >Accessibility Needs</span
          >
        </div>
        <div class="flex flex-wrap gap-3">
          {#each accessibilityOptions as option}
            <button
              type="button"
              onclick={() => toggleAccessibility(option)}
              class="btn btn-sm gap-2 rounded-full {selectedAccessibility.includes(
                option,
              )
                ? 'btn-ghost bg-primary/10 text-primary hover:bg-primary/20 border border-primary'
                : 'btn-outline border-base-300 text-base-content/60 hover:text-white hover:border-primary/50'}"
            >
              {option}
              <span class="material-symbols-outlined text-sm"
                >{selectedAccessibility.includes(option)
                  ? "close"
                  : "add"}</span
              >
            </button>
          {/each}
        </div>
        {#if selectedAccessibility.includes("Other")}
          <input
            type="text"
            name="otherAccessibility"
            bind:value={otherAccessibility}
            placeholder="Please specify other accessibility needs"
            class="input input-bordered w-full bg-base-100 mt-3"
          />
        {/if}
      </div>

      <!-- Hidden input to store selected accessibility -->
      <input
        type="hidden"
        name="selectedAccessibility"
        value={JSON.stringify(selectedAccessibility)}
      />

      <div class="form-control">
        <div class="label">
          <span class="label-text font-medium text-white"
            >Deal-breakers or Hard No's</span
          >
        </div>
        <textarea
          name="hardNos"
          bind:value={hardNos}
          class="textarea textarea-bordered h-24 bg-base-100"
          placeholder="e.g. No camping, no red-eye flights, must have WiFi..."
        ></textarea>
      </div>
    </section>

    <!-- Section 5: Additional Notes -->
    <section
      class="flex flex-col gap-6 p-6 md:p-8 rounded-2xl bg-base-200 border border-base-300"
    >
      <div class="flex items-center gap-3 mb-2">
        <div
          class="size-8 rounded-full bg-primary/20 flex items-center justify-center text-primary font-bold"
        >
          5
        </div>
        <h2 class="text-xl font-bold text-white">
          Anything else we should know?
        </h2>
      </div>

      <div class="form-control">
        <textarea
          name="additionalNotes"
          bind:value={additionalNotes}
          class="textarea textarea-bordered h-32 bg-base-100"
          placeholder="Any other preferences, ideas, or concerns..."
        ></textarea>
      </div>
    </section>

    <!-- Actions Footer (Sticky) -->
    <div
      class="fixed bottom-0 left-0 lg:left-80 right-0 p-4 bg-base-100/90 backdrop-blur-md border-t border-base-300 flex items-center justify-between z-40"
    >
      <a
        href="/trips/{data.trip.id}"
        class="btn btn-ghost font-bold text-base-content/60 hover:text-white"
      >
        Back
      </a>
      <button
        type="submit"
        disabled={submitting}
        class="btn btn-primary rounded-full px-8 text-base-300 font-bold shadow-lg shadow-primary/20 gap-2"
      >
        {submitting ? "Saving..." : "Sync Preferences"}
        {#if !submitting}
          <span class="material-symbols-outlined text-lg">arrow_forward</span>
        {/if}
      </button>
    </div>
  </form>
</div>
