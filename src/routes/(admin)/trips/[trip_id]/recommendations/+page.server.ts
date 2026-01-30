import { error } from "@sveltejs/kit"
import type { PageServerLoad } from "./$types"

export const load: PageServerLoad = async ({ params, locals: { supabase, session } }) => {
  if (!session) {
    throw error(401, "Unauthorized")
  }

  const { trip_id } = params

  // Load trip details
  const { data: trip, error: tripError } = await supabase
    .from("trips")
    .select("*")
    .eq("id", trip_id)
    .single()

  if (tripError || !trip) {
    throw error(404, "Trip not found")
  }

  // Check if user is a member of this trip
  const { data: membership, error: membershipError } = await supabase
    .from("trip_members")
    .select("role")
    .eq("trip_id", trip_id)
    .eq("user_id", session.user.id)
    .single()

  if (membershipError || !membership) {
    throw error(403, "You are not a member of this trip")
  }

  // Load recommendations (if they exist)
  const { data: recommendations, error: recsError } = await supabase
    .from("recommendations")
    .select("*")
    .eq("trip_id", trip_id)
    .order("generated_at", { ascending: false })
    .limit(1)
    .single()

  if (recsError && recsError.code !== "PGRST116") {
    console.error("Error loading recommendations:", recsError)
  }

  // Load trip members
  const { data: members, error: membersError } = await supabase
    .from("trip_members")
    .select("user_id, role")
    .eq("trip_id", trip_id)

  if (membersError) {
    console.error("Error loading members:", membersError)
  }

  // Load profiles for members
  const memberUserIds = members?.map(m => m.user_id) || []
  const { data: profiles, error: profilesError } = await supabase
    .from("profiles")
    .select("id, full_name, avatar_url")
    .in("id", memberUserIds)

  if (profilesError) {
    console.error("Error loading profiles:", profilesError)
  }

  // Check which members have submitted preferences
  const { data: preferencesData, error: prefsError } = await supabase
    .from("preferences")
    .select("user_id")
    .eq("trip_id", trip_id)

  if (prefsError) {
    console.error("Error loading preferences:", prefsError)
  }

  const userIdsWithPrefs = new Set(preferencesData?.map(p => p.user_id) || [])
  const profilesMap = new Map(profiles?.map(p => [p.id, p]) || [])

  // Combine member data with preference status
  const membersWithStatus = members?.map(member => {
    const profile = profilesMap.get(member.user_id)
    return {
      user_id: member.user_id,
      role: member.role,
      full_name: profile?.full_name || null,
      avatar_url: profile?.avatar_url || null,
      has_preferences: userIdsWithPrefs.has(member.user_id)
    }
  }) || []

  return {
    trip,
    recommendations: recommendations || null,
    userRole: membership.role,
    members: membersWithStatus,
    session
  }
}
