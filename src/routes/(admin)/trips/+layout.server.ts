import type { LayoutServerLoad } from "./$types"
import { redirect } from "@sveltejs/kit"

export const load: LayoutServerLoad = async ({ locals: { supabase, session } }) => {
  if (!session) {
    throw redirect(303, "/login")
  }

  // Load user profile for sidebar
  const { data: profile } = await supabase
    .from("profiles")
    .select("full_name, avatar_url")
    .eq("id", session.user.id)
    .single()

  return {
    session,
    profile: profile || {
      full_name: session.user.email?.split("@")[0] || "User",
      avatar_url: null
    },
    userEmail: session.user.email
  }
}
