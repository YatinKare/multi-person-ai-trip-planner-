<script lang="ts">
  import { enhance } from "$app/forms"

  interface Props {
    show: boolean
    tripId: string
    totalDays: number
    onClose: () => void
    actionData?: any
  }

  let { show, tripId, totalDays, onClose, actionData }: Props = $props()

  // Form fields
  let dayIndex = $state(0)
  let timeSlot = $state("morning")
  let activityName = $state("")
  let activityDescription = $state("")
  let estimatedCost = $state("")
  let location = $state("")
  let reason = $state("")
  let isSubmitting = $state(false)

  // Reset form when closed
  function handleClose() {
    dayIndex = 0
    timeSlot = "morning"
    activityName = ""
    activityDescription = ""
    estimatedCost = ""
    location = ""
    reason = ""
    isSubmitting = false
    onClose()
  }

  // Get day labels
  function getDayLabel(index: number): string {
    return `Day ${index + 1}`
  }

  // Time slot options
  const timeSlots = [
    { value: "morning", label: "Morning", icon: "wb_sunny" },
    { value: "afternoon", label: "Afternoon", icon: "light_mode" },
    { value: "evening", label: "Evening", icon: "nightlight" },
  ]
</script>

{#if show}
  <div class="modal modal-open">
    <div class="modal-box max-w-2xl">
      <h3 class="font-bold text-2xl mb-4 flex items-center gap-2">
        <span class="material-symbols-outlined text-primary">add_circle</span>
        Suggest Activity
      </h3>

      <p class="text-base-content/80 mb-6">
        Have an activity idea? Suggest it here and the organizer will review your suggestion.
      </p>

      {#if actionData && "error" in actionData && actionData.action === "suggestActivity"}
        <div class="alert alert-error mb-4">
          <span class="material-symbols-outlined">error</span>
          <span>{actionData.error}</span>
        </div>
      {/if}

      {#if actionData && "success" in actionData && actionData.action === "suggestActivity"}
        <div class="alert alert-success mb-4">
          <span class="material-symbols-outlined">check_circle</span>
          <span>Activity suggestion submitted successfully!</span>
        </div>
      {/if}

      <form
        method="POST"
        action="?/suggestActivity"
        use:enhance={() => {
          isSubmitting = true
          return async ({ update }) => {
            await update()
            isSubmitting = false
            // Close modal on success
            if (actionData && "success" in actionData) {
              handleClose()
            }
          }
        }}
      >
        <input type="hidden" name="tripId" value={tripId} />

        <div class="space-y-4">
          <!-- Day Selection -->
          <div class="form-control">
            <label class="label">
              <span class="label-text font-semibold">Which day? <span class="text-error">*</span></span>
            </label>
            <select
              name="dayIndex"
              bind:value={dayIndex}
              class="select select-bordered w-full"
              required
            >
              {#each Array(totalDays) as _, i}
                <option value={i}>{getDayLabel(i)}</option>
              {/each}
            </select>
          </div>

          <!-- Time Slot Selection -->
          <div class="form-control">
            <label class="label">
              <span class="label-text font-semibold">Time slot <span class="text-error">*</span></span>
            </label>
            <div class="grid grid-cols-3 gap-2">
              {#each timeSlots as slot}
                <label class="cursor-pointer">
                  <input
                    type="radio"
                    name="timeSlot"
                    value={slot.value}
                    bind:group={timeSlot}
                    class="hidden peer"
                    required
                  />
                  <div
                    class="btn btn-outline w-full peer-checked:btn-primary peer-checked:btn-active flex items-center gap-2"
                  >
                    <span class="material-symbols-outlined text-lg">{slot.icon}</span>
                    <span class="text-sm">{slot.label}</span>
                  </div>
                </label>
              {/each}
            </div>
          </div>

          <!-- Activity Name -->
          <div class="form-control">
            <label class="label">
              <span class="label-text font-semibold">Activity name <span class="text-error">*</span></span>
            </label>
            <input
              type="text"
              name="activityName"
              bind:value={activityName}
              placeholder="e.g., Visit local art museum"
              class="input input-bordered w-full"
              required
              maxlength="200"
            />
          </div>

          <!-- Activity Description -->
          <div class="form-control">
            <label class="label">
              <span class="label-text font-semibold">Description</span>
            </label>
            <textarea
              name="activityDescription"
              bind:value={activityDescription}
              placeholder="Add details about the activity..."
              class="textarea textarea-bordered h-24 w-full"
              maxlength="500"
            ></textarea>
          </div>

          <!-- Location and Cost (side by side) -->
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="form-control">
              <label class="label">
                <span class="label-text font-semibold">Location</span>
              </label>
              <input
                type="text"
                name="location"
                bind:value={location}
                placeholder="e.g., Downtown area"
                class="input input-bordered w-full"
                maxlength="200"
              />
            </div>

            <div class="form-control">
              <label class="label">
                <span class="label-text font-semibold">Estimated cost per person</span>
              </label>
              <div class="join w-full">
                <span class="btn btn-outline join-item pointer-events-none">$</span>
                <input
                  type="number"
                  name="estimatedCost"
                  bind:value={estimatedCost}
                  placeholder="0"
                  class="input input-bordered join-item flex-1"
                  min="0"
                  step="0.01"
                />
              </div>
            </div>
          </div>

          <!-- Reason for Suggestion -->
          <div class="form-control">
            <label class="label">
              <span class="label-text font-semibold">Why are you suggesting this?</span>
            </label>
            <textarea
              name="reason"
              bind:value={reason}
              placeholder="Optional: Explain why this would be a great addition..."
              class="textarea textarea-bordered h-20 w-full"
              maxlength="300"
            ></textarea>
          </div>
        </div>

        <!-- Actions -->
        <div class="modal-action">
          <button
            type="button"
            class="btn btn-ghost"
            onclick={handleClose}
            disabled={isSubmitting}
          >
            Cancel
          </button>
          <button
            type="submit"
            class="btn btn-primary gap-2"
            disabled={isSubmitting || !activityName.trim()}
          >
            {#if isSubmitting}
              <span class="loading loading-spinner loading-sm"></span>
              Submitting...
            {:else}
              <span class="material-symbols-outlined">send</span>
              Submit Suggestion
            {/if}
          </button>
        </div>
      </form>
    </div>
    <button
      type="button"
      class="modal-backdrop"
      onclick={handleClose}
      aria-label="Close modal"
    ></button>
  </div>
{/if}
