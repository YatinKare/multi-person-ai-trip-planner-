import {
  PUBLIC_SUPABASE_ANON_KEY,
  PUBLIC_SUPABASE_URL,
} from "$env/static/public"
import {
  createBrowserClient,
  createServerClient,
  isBrowser,
} from "@supabase/ssr"
import { redirect } from "@sveltejs/kit"
import type { LayoutLoad } from "./$types"

export const load: LayoutLoad = async ({ fetch, data, depends }) => {
  depends("supabase:auth")

  const supabase = isBrowser()
    ? createBrowserClient(PUBLIC_SUPABASE_URL, PUBLIC_SUPABASE_ANON_KEY, {
        global: {
          fetch,
        },
      })
    : createServerClient(PUBLIC_SUPABASE_URL, PUBLIC_SUPABASE_ANON_KEY, {
        global: {
          fetch,
        },
        cookies: {
          getAll() {
            return data.cookies
          },
        },
      })

  if (!data.session) {
    redirect(303, "/login")
  }

  return {
    supabase,
    session: data.session,
    profile: data.profile,
    userEmail: data.userEmail,
  }
}
