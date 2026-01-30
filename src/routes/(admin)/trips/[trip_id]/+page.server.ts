import { error, redirect, fail } from "@sveltejs/kit"
import type { PageServerLoad, Actions } from "./$types"
import { aggregatePreferences } from "$lib/server/aggregatePreferences"

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


  // Load preferences for all members to determine response status and aggregation
  const { data: preferences, error: preferencesError } = await supabase
    .from("preferences")
    .select("*")
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

  // Aggregate preferences if any exist
  const aggregated = preferences && preferences.length > 0
    ? aggregatePreferences(preferences)
    : null

  // Check if recommendations already exist
  const { data: existingRecommendations, error: recsError } = await supabase
    .from("recommendations")
    .select("id, generated_at")
    .eq("trip_id", trip_id)
    .order("generated_at", { ascending: false })
    .limit(1)
    .single()

  if (recsError && recsError.code !== "PGRST116") {
    console.error("Error loading recommendations:", recsError)
  }

  return {
    trip,
    members: membersWithStatus,
    userRole: membership.role,
    responseCount,
    totalMembers,
    userId: session.user.id,
    aggregated,
    hasRecommendations: !!existingRecommendations,
    session,
    supabase
  }
}

export const actions: Actions = {
  deleteTrip: async ({ request, params, locals: { supabase, session } }) => {
    if (!session) {
      return fail(401, { message: "Unauthorized" })
    }

    const { trip_id } = params
    const formData = await request.formData()
    const confirmation = formData.get("confirmation") as string

    // Verify user is the organizer
    const { data: membership, error: membershipError } = await supabase
      .from("trip_members")
      .select("role")
      .eq("trip_id", trip_id)
      .eq("user_id", session.user.id)
      .single()

    if (membershipError || !membership) {
      return fail(403, { message: "You are not a member of this trip" })
    }

    if (membership.role !== "organizer") {
      return fail(403, { message: "Only organizers can delete trips" })
    }

    // Get trip name for confirmation validation
    const { data: trip, error: tripError } = await supabase
      .from("trips")
      .select("name")
      .eq("id", trip_id)
      .single()

    if (tripError || !trip) {
      return fail(404, { message: "Trip not found" })
    }

    // Validate confirmation text
    if (confirmation.trim() !== trip.name.trim()) {
      return fail(400, { message: "Trip name does not match. Please type the exact trip name." })
    }

    // Delete the trip (cascading deletes will handle related records)
    const { error: deleteError } = await supabase
      .from("trips")
      .delete()
      .eq("id", trip_id)

    if (deleteError) {
      console.error("Error deleting trip:", deleteError)
      return fail(500, { message: "Failed to delete trip. Please try again." })
    }

    // Redirect to trips list page
    throw redirect(303, "/trips")
  },

  leaveTrip: async ({ params, locals: { supabase, session } }) => {
    if (!session) {
      return fail(401, { message: "Unauthorized" })
    }

    const { trip_id } = params

    // Verify user is a member of this trip
    const { data: membership, error: membershipError } = await supabase
      .from("trip_members")
      .select("role")
      .eq("trip_id", trip_id)
      .eq("user_id", session.user.id)
      .single()

    if (membershipError || !membership) {
      return fail(403, { message: "You are not a member of this trip" })
    }

    // Prevent organizer from leaving
    if (membership.role === "organizer") {
      return fail(403, { message: "Organizers cannot leave trips. Please delete the trip or transfer ownership." })
    }

    // Delete user's preferences for this trip
    const { error: preferencesError } = await supabase
      .from("preferences")
      .delete()
      .eq("trip_id", trip_id)
      .eq("user_id", session.user.id)

    if (preferencesError) {
      console.error("Error deleting preferences:", preferencesError)
      // Continue anyway - preferences might not exist
    }

    // Remove user from trip_members
    const { error: leaveError } = await supabase
      .from("trip_members")
      .delete()
      .eq("trip_id", trip_id)
      .eq("user_id", session.user.id)

    if (leaveError) {
      console.error("Error leaving trip:", leaveError)
      return fail(500, { message: "Failed to leave trip. Please try again." })
    }

    // Redirect to trips list page
    throw redirect(303, "/trips")
  }
}
