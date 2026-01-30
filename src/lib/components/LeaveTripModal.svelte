<script lang="ts">
  import { enhance } from "$app/forms"
  import type { SubmitFunction } from "@sveltejs/kit"

  export let open = false
  export let tripName: string
  export let tripId: string

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
        // Modal will close, user will be redirected by the server action
        closeModal()
      } else if (result.type === "failure") {
        errorMessage =
          result.data?.message || "Failed to leave trip. Please try again."
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

        <!-- Warning Icon -->
        <div class="text-center mb-6">
          <div class="inline-block relative">
            <span
              class="material-symbols-outlined text-7xl text-warning"
              style="font-variation-settings: 'FILL' 1;"
            >
              logout
            </span>
            <div
              class="absolute inset-0 bg-warning/20 blur-xl rounded-full"
            ></div>
          </div>
          <h2 class="text-3xl font-bold mt-4 text-warning">Leave Trip?</h2>
          <p class="text-base-content/70 mt-2">
            Are you sure you want to leave {tripName}?
          </p>
        </div>

        <!-- Warning Details -->
        <div class="alert alert-warning mb-6">
          <span class="material-symbols-outlined">info</span>
          <div class="text-sm">
            <p class="font-semibold">If you leave this trip:</p>
            <ul class="list-disc list-inside mt-2 space-y-1">
              <li>Your preferences will be deleted</li>
              <li>You will no longer see trip updates</li>
              <li>You'll need a new invite link to rejoin</li>
            </ul>
          </div>
        </div>

        <!-- Confirmation Form -->
        <form method="POST" action="?/leaveTrip" use:enhance={handleSubmit}>
          <input type="hidden" name="tripId" value={tripId} />

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
              class="btn btn-warning flex-1 font-semibold"
            >
              {#if isSubmitting}
                <span class="loading loading-spinner"></span>
                Leaving...
              {:else}
                Leave Trip
              {/if}
            </button>
          </div>
        </form>

        <div
          class="mt-4 h-1 w-full bg-gradient-to-r from-warning/0 via-warning/50 to-warning/0 rounded-full"
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
