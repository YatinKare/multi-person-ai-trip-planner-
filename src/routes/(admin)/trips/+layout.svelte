<script lang="ts">
  import { page } from "$app/stores"
  import type { Snippet } from "svelte"
  import type { LayoutData } from "./$types"

  interface Props {
    data: LayoutData
    children: Snippet
  }

  let { data, children }: Props = $props()

  // Determine active menu item based on current path
  const isTripsActive = $derived($page.url.pathname === "/trips" || $page.url.pathname.startsWith("/trips/"))

  // Close drawer on mobile after navigation
  function closeDrawer(): void {
    const drawer = document.getElementById("trips-drawer") as HTMLInputElement
    if (drawer) {
      drawer.checked = false
    }
  }
</script>

<div class="drawer lg:drawer-open" data-theme="tripsync">
  <input id="trips-drawer" type="checkbox" class="drawer-toggle" />

  <!-- Main content area -->
  <div class="drawer-content flex flex-col min-h-screen bg-base-100">
    <!-- Mobile navbar -->
    <div class="navbar bg-base-200 border-b border-base-300 lg:hidden">
      <label for="trips-drawer" class="btn btn-ghost btn-square">
        <span class="material-symbols-outlined">menu</span>
      </label>
      <span class="flex-1 text-xl font-bold">TripSync</span>
      <div class="avatar">
        <div class="w-10 rounded-full">
          {#if data.profile?.avatar_url}
            <img src={data.profile.avatar_url} alt={data.profile.full_name || "User"} />
          {:else}
            <div class="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center">
              <span class="material-symbols-outlined text-primary">person</span>
            </div>
          {/if}
        </div>
      </div>
    </div>

    <!-- Page content -->
    <main class="flex-1 p-6 lg:p-10">
      {@render children()}
    </main>
  </div>

  <!-- Sidebar -->
  <div class="drawer-side z-40">
    <label for="trips-drawer" aria-label="close sidebar" class="drawer-overlay"></label>
    <aside class="bg-base-200 w-72 min-h-full border-r border-base-300 flex flex-col">
      <!-- Logo -->
      <div class="p-6 flex items-center gap-3">
        <div class="bg-primary/20 p-2 rounded-lg text-primary">
          <span class="material-symbols-outlined text-2xl">flight_takeoff</span>
        </div>
        <h1 class="text-xl font-bold">TripSync</h1>
      </div>

      <!-- Menu -->
      <ul class="menu flex-1 px-4 gap-1">
        <li>
          <a
            href="/account"
            class="flex items-center gap-3"
            onclick={closeDrawer}
          >
            <span class="material-symbols-outlined">dashboard</span>
            Dashboard
          </a>
        </li>
        <li>
          <a
            href="/trips"
            class={isTripsActive ? "active bg-primary/10 text-primary font-bold" : "flex items-center gap-3"}
            onclick={closeDrawer}
          >
            <span class="material-symbols-outlined {isTripsActive ? 'filled' : ''}">map</span>
            My Trips
          </a>
        </li>
        <li>
          <button
            class="flex items-center gap-3"
            onclick={closeDrawer}
          >
            <span class="material-symbols-outlined">notifications</span>
            Notifications
            <span class="badge badge-primary badge-sm ml-auto">3</span>
          </button>
        </li>
        <li>
          <a
            href="/account/settings"
            class="flex items-center gap-3"
            onclick={closeDrawer}
          >
            <span class="material-symbols-outlined">settings</span>
            Settings
          </a>
        </li>
      </ul>

      <!-- User profile -->
      <div class="p-4 border-t border-base-300">
        <a
          href="/account/settings/edit_profile"
          class="flex items-center gap-3 p-3 rounded-xl bg-base-300 hover:bg-base-100/50 transition-colors"
        >
          <div class="avatar">
            <div class="w-10 rounded-full">
              {#if data.profile?.avatar_url}
                <img src={data.profile.avatar_url} alt={data.profile.full_name || "User"} />
              {:else}
                <div class="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center">
                  <span class="material-symbols-outlined text-primary">person</span>
                </div>
              {/if}
            </div>
          </div>
          <div class="flex flex-col overflow-hidden">
            <p class="truncate text-sm font-bold">{data.profile?.full_name || "User"}</p>
            <p class="truncate text-xs text-base-content/60">{data.userEmail || ""}</p>
          </div>
        </a>
      </div>
    </aside>
  </div>
</div>
