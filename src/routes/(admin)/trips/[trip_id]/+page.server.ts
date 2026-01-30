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

  // Load all trip members
  const { data: members, error: membersError } = await supabase
    .from("trip_members")
    .select("user_id, role, joined_at")
    .eq("trip_id", trip_id)
    .order("joined_at", { ascending: true })

  if (membersError) {
    console.error("Error loading members:", membersError)
  }

  // Load profiles for all members
  const userIds = members?.map(m => m.user_id) || []
  const { data: profiles, error: profilesError } = await supabase
    .from("profiles")
    .select("id, full_name, avatar_url")
    .in("id", userIds)

  if (profilesError) {
    console.error("Error loading profiles:", profilesError)
  }

  // Create a map of user_id to profile
  const profileMap = new Map(profiles?.map(p => [p.id, p]))


  // Load preferences for all members to determine response status
  const { data: preferences, error: preferencesError } = await supabase
    .from("preferences")
    .select("user_id, submitted_at")
    .eq("trip_id", trip_id)

  if (preferencesError) {
    console.error("Error loading preferences:", preferencesError)
  }

  // Combine member info with response status
  const membersWithStatus = (members || []).map(member => {
    const hasResponded = preferences?.some(p => p.user_id === member.user_id)
    const profile = profileMap.get(member.user_id)
    return {
      user_id: member.user_id,
      role: member.role,
      joined_at: member.joined_at,
      profile: profile || null,
      has_responded: hasResponded
    }
  })

  // Count responses
  const responseCount = membersWithStatus.filter(m => m.has_responded).length
  const totalMembers = membersWithStatus.length

  return {
    trip,
    members: membersWithStatus,
    userRole: membership.role,
    responseCount,
    totalMembers,
    userId: session.user.id,
    session,
    supabase
  }
}
