<script lang="ts">
  import { enhance } from "$app/forms"
  import type { PageData } from "./$types"

  let { data }: { data: PageData } = $props()

  // Determine trip timeframe display
  const tripTimeframe = $derived(() => {
    if (data.trip?.rough_timeframe) {
      return data.trip.rough_timeframe
    }
    return null
  })

  let isSubmitting = $state(false)
</script>

<svelte:head>
  <title>{data.trip ? `Join ${data.trip.name}` : "Join Trip"} - TripSync</title>
</svelte:head>

<!-- Main Container -->
<div
  class="relative flex min-h-screen w-full flex-col overflow-hidden"
  data-theme="tripsync"
>
  <!-- Background Image with Overlay -->
  <div class="absolute inset-0 z-0">
    <div
      class="absolute inset-0 bg-gradient-to-b from-black/60 via-black/40 to-base-100/90 z-10"
    ></div>
    <div
      class="h-full w-full bg-cover bg-center bg-no-repeat transition-transform duration-1000 hover:scale-105"
      style="background-image: url('https://lh3.googleusercontent.com/aida-public/AB6AXuBYihKFGtj5WlZMFr7zinr7shq54XG9mj95ic61U0g14ejB62zLz8U1PHmw8iqD6_0VOXkuFgwsBBQCRrBXsH3aZuW5tSQCGUbNSqQL7Nb7_hj5Y1i893feQCm7DPSl3N9H8_8bJgafO8liA_s6L4VgrZYeDQFsNXuLCH-yj3TzaSI_LTL0xRsaK81OHAamh0QeBjWojNJBrWlyCtT4F5pxxmsdSUugUE7n7hZ2IhC_vuMTFRYNQX5jem5jP5QEB9prOp3e0bYMoayF');"
    ></div>
  </div>

  <!-- Navbar -->
  <header
    class="relative z-20 flex items-center justify-between px-6 py-4 md:px-10 lg:px-40"
  >
    <a href="/" class="flex items-center gap-2 cursor-pointer">
      <div
        class="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-base-300"
      >
        <span class="material-symbols-outlined text-xl font-bold"
          >flight_takeoff</span
        >
      </div>
      <h2 class="text-white text-xl font-bold tracking-tight">TripSync</h2>
    </a>
    {#if !data.session}
      <a
        href="/login"
        class="hidden md:flex btn btn-ghost btn-sm text-white hover:bg-white/10"
      >
        Sign In
      </a>
    {/if}
  </header>

  <!-- Main Content Area -->
  <main
    class="relative z-20 flex flex-1 flex-col items-center justify-center px-4 py-10 md:px-6"
  >
    {#if data.error || !data.trip}
      <!-- Error State -->
      <div
        class="w-full max-w-[480px] overflow-hidden rounded-2xl border border-white/10 bg-base-300/95 shadow-2xl backdrop-blur-sm p-8 text-center"
      >
        <span class="material-symbols-outlined text-6xl text-error mb-4"
          >error_outline</span
        >
        <h1 class="text-2xl font-bold text-white mb-2">Invalid Invite Link</h1>
        <p class="text-base-content/60 mb-6">
          This invite link is invalid or has expired. Please ask the trip
          organizer for a new link.
        </p>
        <a href="/" class="btn btn-primary">Go to Home</a>
      </div>
    {:else}
      <!-- Invitation Card -->
      <div
        class="w-full max-w-[480px] overflow-hidden rounded-2xl border border-white/10 bg-base-300/95 shadow-2xl backdrop-blur-sm transition-all animate-fade-in-up"
      >
        <!-- Card Header Image (Mini Hero) -->
        <div
          class="relative h-32 w-full bg-cover bg-center"
          style="background-image: url('https://lh3.googleusercontent.com/aida-public/AB6AXuDrviQHynNJeX-11u7ooWodZG8v6Qk33AWDAIVRK_o4KAU1r858_KLWe3ybu40o1Va37ajo8YNK0DZCaO1skIHOcmzj3PIvwgbRH8seyMHOU5FtFMRkoHicU7DpfJYQhtu-13W4-4sZ6eNBrO8-bhJRHjMjC1XCvMtgF8u8ZxZljFToYDP5o2mqAqpNG7AcsBcRi5QaccZg9xBCeZzmv2eX-a89ifzmr-izMoRigEj9mVpb_aTAmtA_qkPy_S5e76TPn54Z2qd-qowO');"
        >
          <div
            class="absolute inset-0 bg-gradient-to-t from-base-300 to-transparent"
          ></div>
          <div class="absolute bottom-4 left-6">
            <span
              class="badge badge-primary badge-outline bg-primary/20 backdrop-blur-md gap-1 font-bold"
            >
              <span class="material-symbols-outlined text-[14px]"
                >auto_awesome</span
              >
              AI-Powered Itinerary
            </span>
          </div>
        </div>

        <!-- Card Body -->
        <div class="flex flex-col gap-6 px-6 pb-8 pt-2">
          <!-- Trip Title & Intro -->
          <div class="text-center">
            <p
              class="mb-1 text-sm font-medium uppercase tracking-wider text-base-content/60"
            >
              You're invited to
            </p>
            <h1
              class="text-3xl font-black leading-tight tracking-tight text-white md:text-4xl"
            >
              {data.trip.name}
            </h1>
            {#if tripTimeframe()}
              <div
                class="mt-2 flex items-center justify-center gap-2 text-sm text-base-content/60"
              >
                <span class="material-symbols-outlined text-[18px] text-primary"
                  >calendar_month</span
                >
                <span>{tripTimeframe()}</span>
              </div>
            {/if}
          </div>
          <div class="divider my-0"></div>

          <!-- Organizer Section -->
          <div class="flex flex-col items-center gap-3">
            <div class="relative">
              <div class="avatar">
                <div
                  class="w-20 rounded-full ring ring-primary ring-offset-base-100 ring-offset-2"
                >
                  {#if data.trip.organizer?.avatar_url}
                    <img
                      src={data.trip.organizer.avatar_url}
                      alt={data.trip.organizer.full_name || "Organizer"}
                    />
                  {:else}
                    <div
                      class="w-20 h-20 rounded-full bg-primary/20 flex items-center justify-center"
                    >
                      <span
                        class="material-symbols-outlined text-4xl text-primary"
                        >person</span
                      >
                    </div>
                  {/if}
                </div>
              </div>
              <div
                class="absolute -bottom-1 -right-1 flex h-8 w-8 items-center justify-center rounded-full bg-base-300 text-primary shadow-sm border border-base-200"
              >
                <span class="material-symbols-outlined text-[18px]"
                  >verified</span
                >
              </div>
            </div>
            <div class="text-center">
              <p class="text-lg font-bold text-white">
                Invited by {data.trip.organizer?.full_name || "Trip Organizer"}
              </p>
              <p class="text-sm text-base-content/60">Trip Organizer</p>
            </div>
          </div>

          <!-- Social Proof / Attendees -->
          {#if data.memberCount > 0}
            <div class="rounded-xl bg-base-100/50 p-4 border border-white/5">
              <div
                class="flex flex-col items-center justify-center gap-3 md:flex-row md:justify-between"
              >
                <div class="avatar-group -space-x-4 rtl:space-x-reverse">
                  {#each data.otherMembers.slice(0, 3) as member}
                    <div class="avatar border-white/10">
                      <div class="w-10">
                        {#if member.avatar_url}
                          <img
                            src={member.avatar_url}
                            alt={member.full_name || "Member"}
                          />
                        {:else}
                          <div
                            class="w-10 h-10 rounded-full bg-neutral flex items-center justify-center"
                          >
                            <span
                              class="material-symbols-outlined text-sm text-neutral-content"
                              >person</span
                            >
                          </div>
                        {/if}
                      </div>
                    </div>
                  {/each}
                  {#if data.memberCount > 3}
                    <div class="avatar placeholder border-white/10">
                      <div class="w-10 bg-neutral text-neutral-content">
                        <span class="text-xs">+{data.memberCount - 3}</span>
                      </div>
                    </div>
                  {/if}
                </div>
                <p class="text-sm font-medium text-white/90">
                  {#if data.otherMembers.length > 0}
                    Join {data.otherMembers[0]?.full_name?.split(" ")[0] ||
                      "others"}
                    {#if data.memberCount > 1}
                      & {data.memberCount - 1}
                      {data.memberCount === 2 ? "other" : "others"}
                    {/if}
                  {:else}
                    Be the first to join!
                  {/if}
                </p>
              </div>
            </div>
          {/if}

          <!-- Actions -->
          <div class="flex flex-col gap-3">
            <form
              method="POST"
              action="?/joinTrip"
              use:enhance={() => {
                isSubmitting = true
                return async ({ update }) => {
                  await update()
                  isSubmitting = false
                }
              }}
            >
              <button
                type="submit"
                disabled={isSubmitting}
                class="btn btn-primary w-full h-auto py-3.5 text-base font-bold text-base-300 shadow-lg shadow-primary/20 gap-3"
              >
                {#if !data.session}
                  <!-- Google Icon SVG -->
                  <svg
                    class="h-5 w-5"
                    viewBox="0 0 24 24"
                    xmlns="http://www.w3.org/2000/svg"
                  >
                    <path
                      d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                      fill="#4285F4"
                    ></path>
                    <path
                      d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                      fill="#34A853"
                    ></path>
                    <path
                      d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                      fill="#FBBC05"
                    ></path>
                    <path
                      d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                      fill="#EA4335"
                    ></path>
                  </svg>
                  Join Trip with Google
                {:else if isSubmitting}
                  <span class="loading loading-spinner loading-sm"></span>
                  Joining...
                {:else}
                  <span class="material-symbols-outlined">group_add</span>
                  Join Trip
                {/if}
              </button>
            </form>
            <div class="text-center">
              <span class="text-sm text-base-content/60"
                >Already have an account?
              </span>
              <a
                href="/login?redirectTo=/join/{data.trip.invite_code}"
                class="link link-hover text-sm font-bold text-white hover:text-primary transition-colors"
              >
                Sign In
              </a>
            </div>
          </div>
        </div>
      </div>

      <!-- Mobile Sign In (only visible on small screens below card) -->
      <div class="mt-8 md:hidden">
        <a
          href="/login?redirectTo=/join/{data.trip.invite_code}"
          class="link link-hover text-sm font-bold text-white hover:text-primary transition-colors"
        >
          Sign into existing account
        </a>
      </div>
    {/if}
  </main>
</div>

<style>
  @keyframes fade-in-up {
    from {
      opacity: 0;
      transform: translateY(20px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  .animate-fade-in-up {
    animation: fade-in-up 0.5s ease-out;
  }
</style>
