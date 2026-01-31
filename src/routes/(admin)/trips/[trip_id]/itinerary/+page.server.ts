import { error, fail, redirect } from "@sveltejs/kit"
import type { PageServerLoad, Actions } from "./$types"

export const load: PageServerLoad = async ({
  params,
  locals: { supabase, session },
}) => {
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

  // Load itinerary (if it exists)
  const { data: itinerary, error: itineraryError } = await supabase
    .from("itineraries")
    .select("*")
    .eq("trip_id", trip_id)
    .order("generated_at", { ascending: false })
    .limit(1)
    .maybeSingle()

  if (itineraryError && itineraryError.code !== "PGRST116") {
    console.error("Error loading itinerary:", itineraryError)
  }

  if (!itinerary) {
    throw error(404, "No itinerary found for this trip. Please generate one first.")
  }

  // Load trip members for display
  const { data: members, error: membersError } = await supabase
    .from("trip_members")
    .select("user_id, role")
    .eq("trip_id", trip_id)

  if (membersError) {
    console.error("Error loading members:", membersError)
  }

  return {
    trip,
    itinerary,
    userRole: membership.role,
    members: members || [],
    userId: session.user.id,
  }
}

export const actions: Actions = {
  finalize: async ({ params, locals: { supabase, session } }) => {
    if (!session) {
      return fail(401, { error: "Unauthorized" })
    }

    const { trip_id } = params

    // Check if user is the organizer
    const { data: membership, error: membershipError } = await supabase
      .from("trip_members")
      .select("role")
      .eq("trip_id", trip_id)
      .eq("user_id", session.user.id)
      .single()

    if (membershipError || !membership) {
      return fail(403, { error: "You are not a member of this trip" })
    }

    if (membership.role !== "organizer") {
      return fail(403, { error: "Only the organizer can finalize the itinerary" })
    }

    // Update itinerary to set finalized_at and finalized_by
    const { error: itineraryError } = await supabase
      .from("itineraries")
      .update({
        finalized_at: new Date().toISOString(),
        finalized_by: session.user.id,
      })
      .eq("trip_id", trip_id)

    if (itineraryError) {
      console.error("Error finalizing itinerary:", itineraryError)
      return fail(500, {
        error: "Failed to finalize itinerary. Please try again.",
      })
    }

    // Update trip status to 'finalized'
    const { error: tripError } = await supabase
      .from("trips")
      .update({ status: "finalized" })
      .eq("id", trip_id)

    if (tripError) {
      console.error("Error updating trip status:", tripError)
      return fail(500, {
        error: "Failed to update trip status. Please try again.",
      })
    }

    return { success: true }
  },
}
