<script lang="ts">
  import { enhance } from "$app/forms"
  import type { SubmitFunction } from "@sveltejs/kit"

  export let open = false
  export let destinationName: string
  export let destinationIndex: number

  let isSubmitting = false
  let errorMessage = ""

  // Reset state when modal closes
  $: if (!open) {
    setTimeout(() => {
      errorMessage = ""
      isSubmitting = false
    }, 200)
  }

  const handleSubmit: SubmitFunction = () => {
    isSubmitting = true
    errorMessage = ""
    return async ({ result, update }) => {
      isSubmitting = false
      if (result.type === "success") {
        // Modal will close, trip status will be updated
        closeModal()
      } else if (result.type === "failure") {
        errorMessage =
          result.data?.message || "Failed to select destination. Please try again."
      }
      await update()
    }
  }

  function closeModal() {
    open = false
  }
</script>

{#if open}
  <!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
  <div
    class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
    role="dialog"
    aria-modal="true"
    on:click={closeModal}
    on:keydown={(e) => e.key === "Escape" && closeModal()}
  >
    <!-- svelte-ignore a11y_no_static_element_interactions -->
    <div
      class="relative w-full max-w-lg mx-4 bg-base-200 rounded-2xl shadow-2xl transition-all duration-300"
      on:click|stopPropagation
      on:keydown|stopPropagation
    >
      <div class="p-8">
        <button
          type="button"
          class="absolute top-4 right-4 btn btn-ghost btn-sm btn-circle"
          on:click={closeModal}
        >
          <span class="material-symbols-outlined text-xl">close</span>
        </button>

        <!-- Success Icon -->
        <div class="text-center mb-6">
          <div class="inline-block relative">
            <span
              class="material-symbols-outlined text-7xl text-primary"
              style="font-variation-settings: 'FILL' 1;"
            >
              check_circle
            </span>
            <div
              class="absolute inset-0 bg-primary/20 blur-xl rounded-full"
            ></div>
          </div>
          <h2 class="text-3xl font-bold mt-4 text-primary">Select Final Destination?</h2>
          <p class="text-base-content/70 mt-2">
            This will lock in <strong class="text-primary">{destinationName}</strong> as your group's destination.
          </p>
        </div>

        <!-- Info Details -->
        <div class="alert alert-info mb-6">
          <span class="material-symbols-outlined">info</span>
          <div class="text-sm">
            <p class="font-semibold">After selecting this destination:</p>
            <ul class="list-disc list-inside mt-2 space-y-1">
              <li>Voting will be locked</li>
              <li>You can generate a full itinerary</li>
              <li>Members can no longer vote on destinations</li>
            </ul>
          </div>
        </div>

        <!-- Confirmation Form -->
        <form method="POST" action="?/selectDestination" use:enhance={handleSubmit}>
          <input type="hidden" name="destinationIndex" value={destinationIndex} />

          {#if errorMessage}
            <div class="alert alert-error mb-4">
              <span class="material-symbols-outlined">error</span>
              <span class="text-sm">{errorMessage}</span>
            </div>
          {/if}

          <div class="flex gap-3">
            <button
              type="button"
              on:click={closeModal}
              disabled={isSubmitting}
              class="btn btn-ghost flex-1"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              class="btn btn-primary flex-1 font-semibold"
            >
              {#if isSubmitting}
                <span class="loading loading-spinner"></span>
                Selecting...
              {:else}
                Confirm Selection
              {/if}
            </button>
          </div>
        </form>

        <div
          class="mt-4 h-1 w-full bg-gradient-to-r from-primary/0 via-primary/50 to-primary/0 rounded-full"
        ></div>
      </div>
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
