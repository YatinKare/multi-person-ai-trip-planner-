<script lang="ts">
  import { enhance } from "$app/forms"
  import { goto } from "$app/navigation"
  import type { SubmitFunction } from "@sveltejs/kit"

  interface Props {
    open: boolean
  }

  let { open = $bindable(false) }: Props = $props()

  let step = $state<"input" | "success">("input")
  let tripName = $state("")
  let roughTimeframe = $state("")
  let inviteCode = $state("")
  let createdTripId = $state("")
  let isSubmitting = $state(false)

  // Reset state when modal closes
  $effect(() => {
    if (!open) {
      setTimeout(() => {
        step = "input"
        tripName = ""
        roughTimeframe = ""
        inviteCode = ""
        createdTripId = ""
        isSubmitting = false
      }, 200)
    }
  })

  const handleSubmit: SubmitFunction = () => {
    isSubmitting = true
    return async ({ result, update }) => {
      isSubmitting = false
      if (result.type === "success" && result.data) {
        inviteCode = result.data.inviteCode as string
        createdTripId = result.data.tripId as string
        step = "success"
      }
      await update()
    }
  }

  function closeModal() {
    open = false
  }

  function handleBackdropClick() {
    closeModal()
  }

  function handleBackdropKeydown(e: KeyboardEvent) {
    if (e.key === "Escape") {
      closeModal()
    }
  }

  function copyInviteLink() {
    const link = `${window.location.origin}/join/${inviteCode}`
    navigator.clipboard.writeText(link)
  }

  function shareViaWhatsApp() {
    const link = `${window.location.origin}/join/${inviteCode}`
    const text = `Join my trip "${tripName}"!`
    window.open(
      `https://wa.me/?text=${encodeURIComponent(text + " " + link)}`,
      "_blank",
    )
  }

  function shareViaEmail() {
    const link = `${window.location.origin}/join/${inviteCode}`
    const subject = `Join my trip: ${tripName}`
    const body = `I'm planning a trip and would love for you to join!\n\nClick here to join: ${link}`
    window.location.href = `mailto:?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`
  }

  function shareViaSystem() {
    const link = `${window.location.origin}/join/${inviteCode}`
    if (navigator.share) {
      navigator
        .share({
          title: `Join my trip: ${tripName}`,
          text: `I'm planning a trip and would love for you to join!`,
          url: link,
        })
        .catch(() => {
          // User cancelled or share failed
        })
    }
  }

  function goToDashboard() {
    closeModal()
    goto(`/trips/${createdTripId}`)
  }
</script>

<svelte:window onkeydown={(e) => open && handleBackdropKeydown(e)} />

{#if open}
  <div
    class="fixed inset-0 z-50 flex items-center justify-center"
    role="dialog"
    aria-modal="true"
  >
    <!-- Backdrop -->
    <button
      class="absolute inset-0 bg-black/60 backdrop-blur-sm cursor-default w-full h-full border-none m-0 p-0"
      aria-label="Close modal"
      onclick={handleBackdropClick}
      type="button"
    ></button>

    <!-- Modal Content -->
    <!-- svelte-ignore a11y_click_events_have_key_events -->
    <!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
    <div
      class="relative w-full max-w-lg mx-4 bg-base-200 rounded-2xl shadow-2xl border border-base-300 transition-all duration-300 z-10"
      onclick={(e) => e.stopPropagation()}
      role="document"
    >
      {#if step === "input"}
        <!-- Step 1: Input State -->
        <div class="p-8">
          <button
            type="button"
            class="absolute top-4 right-4 btn btn-ghost btn-sm btn-circle"
            onclick={closeModal}
          >
            <span class="material-symbols-outlined text-xl">close</span>
          </button>

          <h2 class="text-3xl font-bold mb-2">Where are we going?</h2>
          <p class="text-base-content/70 mb-6">
            Give your trip a name to get started.
          </p>

          <form method="POST" action="?/createTrip" use:enhance={handleSubmit}>
            <div class="space-y-4">
              <!-- Trip Name Input -->
              <div class="form-control">
                <label for="trip-name" class="label">
                  <span class="label-text font-medium">Trip Name</span>
                </label>
                <div class="relative">
                  <input
                    id="trip-name"
                    name="tripName"
                    type="text"
                    placeholder="e.g. Summer in Italy"
                    bind:value={tripName}
                    required
                    class="input input-bordered w-full pr-12 focus:input-primary"
                  />
                  <span
                    class="material-symbols-outlined absolute right-4 top-1/2 -translate-y-1/2 text-primary"
                  >
                    auto_awesome
                  </span>
                </div>
              </div>

              <!-- Rough Timeframe Input -->
              <div class="form-control">
                <label for="timeframe" class="label">
                  <span class="label-text font-medium">Timeframe / Vibe</span>
                </label>
                <input
                  id="timeframe"
                  name="roughTimeframe"
                  type="text"
                  placeholder="e.g. Late August"
                  bind:value={roughTimeframe}
                  class="input input-bordered w-full focus:input-primary"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={isSubmitting || !tripName.trim()}
              class="btn btn-primary w-full mt-6 text-lg font-semibold"
            >
              {#if isSubmitting}
                <span class="loading loading-spinner"></span>
                Creating...
              {:else}
                Create Trip
              {/if}
            </button>
          </form>

          <div
            class="mt-4 h-1 w-full bg-gradient-to-r from-primary/0 via-primary/50 to-primary/0 rounded-full"
          ></div>
        </div>
      {:else}
        <!-- Step 2: Success State -->
        <div class="p-8">
          <button
            type="button"
            class="absolute top-4 right-4 btn btn-ghost btn-sm btn-circle"
            onclick={closeModal}
          >
            <span class="material-symbols-outlined text-xl">close</span>
          </button>

          <div class="text-center mb-6">
            <div class="inline-block relative">
              <span
                class="material-symbols-outlined text-7xl text-primary"
                style="font-variation-settings: 'FILL' 1;"
              >
                check_circle
              </span>
              <div
                class="absolute inset-0 bg-primary/30 blur-xl rounded-full animate-pulse"
              ></div>
            </div>
            <h2 class="text-3xl font-bold mt-4">{tripName} is ready!</h2>
            <p class="text-base-content/70 mt-2">
              Share this link with your friends to let them join the planning.
            </p>
          </div>

          <!-- Invite Link Section -->
          <div class="bg-base-300 rounded-xl p-4 mb-6">
            <div class="flex items-center gap-2">
              <input
                type="text"
                readonly
                value="{window.location.origin}/join/{inviteCode}"
                class="input input-sm flex-1 bg-base-100 font-mono text-sm"
              />
              <button
                type="button"
                onclick={copyInviteLink}
                class="btn btn-primary btn-sm"
                title="Copy invite link"
              >
                <span class="material-symbols-outlined text-lg"
                  >content_copy</span
                >
              </button>
            </div>
          </div>

          <!-- Social Sharing Options -->
          <div class="divider text-sm text-base-content/50">Or share via</div>
          <div class="grid grid-cols-3 gap-3 mb-6">
            <button
              type="button"
              onclick={shareViaWhatsApp}
              class="btn btn-outline hover:btn-success flex flex-col gap-1 h-auto py-3"
            >
              <span class="material-symbols-outlined text-2xl">chat</span>
              <span class="text-xs">WhatsApp</span>
            </button>
            <button
              type="button"
              onclick={shareViaEmail}
              class="btn btn-outline hover:btn-info flex flex-col gap-1 h-auto py-3"
            >
              <span class="material-symbols-outlined text-2xl">mail</span>
              <span class="text-xs">Email</span>
            </button>
            <button
              type="button"
              onclick={shareViaSystem}
              class="btn btn-outline hover:btn-primary flex flex-col gap-1 h-auto py-3"
            >
              <span class="material-symbols-outlined text-2xl">share</span>
              <span class="text-xs">Share</span>
            </button>
          </div>

          <!-- Navigation -->
          <button
            type="button"
            onclick={goToDashboard}
            class="btn btn-ghost w-full"
          >
            Go to Trip Dashboard
          </button>
        </div>
      {/if}
    </div>
  </div>
{/if}
