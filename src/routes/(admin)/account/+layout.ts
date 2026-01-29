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
import { load_helper } from "$lib/load_helpers"

export const load = async ({ fetch, data, depends }) => {
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

  const { session, user } = await load_helper(data.session, supabase)
  if (!session || !user) {
    redirect(303, "/login")
  }

  const { data: profile } = await supabase
    .from("profiles")
    .select(`*`)
    .eq("id", user.id)
    .single()

  const { data: aal } = await supabase.auth.mfa.getAuthenticatorAssuranceLevel()

  /* Profile check redirection logic removed as requested */
  /*
  const createProfilePath = "/account/create_profile"
  const signOutPath = "/account/sign_out"
  if (
    profile &&
    !_hasFullProfile(profile) &&
    url.pathname !== createProfilePath &&
    url.pathname !== signOutPath &&
    CreateProfileStep
  ) {
    redirect(303, createProfilePath)
  }
  */

  return {
    supabase,
    session,
    profile,
    user,
    amr: aal?.currentAuthenticationMethods,
  }
}
