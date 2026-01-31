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

  // Load feedback for this itinerary
  const { data: feedback, error: feedbackError } = await supabase
    .from("itinerary_feedback")
    .select("*")
    .eq("itinerary_id", itinerary.id)

  if (feedbackError) {
    console.error("Error loading feedback:", feedbackError)
  }

  // Load user's own feedback
  const { data: userFeedback, error: userFeedbackError } = await supabase
    .from("itinerary_feedback")
    .select("*")
    .eq("itinerary_id", itinerary.id)
    .eq("user_id", session.user.id)

  if (userFeedbackError) {
    console.error("Error loading user feedback:", userFeedbackError)
  }

  return {
    trip,
    itinerary,
    userRole: membership.role,
    members: members || [],
    userId: session.user.id,
    feedback: feedback || [],
    userFeedback: userFeedback || [],
  }
}

export const actions: Actions = {
  submitFeedback: async ({ request, params, locals: { supabase, session } }) => {
    if (!session) {
      return fail(401, { error: "Unauthorized" })
    }

    const { trip_id } = params
    const formData = await request.formData()
    const itineraryId = formData.get("itinerary_id") as string
    const dayIndex = parseInt(formData.get("day_index") as string)
    const activityIndex = parseInt(formData.get("activity_index") as string)
    const activityName = formData.get("activity_name") as string
    const reason = formData.get("reason") as string | null

    // Check if user is a member of this trip
    const { data: membership, error: membershipError } = await supabase
      .from("trip_members")
      .select("role")
      .eq("trip_id", trip_id)
      .eq("user_id", session.user.id)
      .single()

    if (membershipError || !membership) {
      return fail(403, { error: "You are not a member of this trip" })
    }

    // Check if trip is finalized (no feedback allowed after finalization)
    const { data: trip, error: tripError } = await supabase
      .from("trips")
      .select("status")
      .eq("id", trip_id)
      .single()

    if (tripError || !trip) {
      return fail(404, { error: "Trip not found" })
    }

    if (trip.status === "finalized") {
      return fail(403, { error: "Cannot submit feedback on finalized itineraries" })
    }

    // Upsert feedback (insert or update if already exists)
    const { error: feedbackError } = await supabase
      .from("itinerary_feedback")
      .upsert(
        {
          itinerary_id: itineraryId,
          user_id: session.user.id,
          day_index: dayIndex,
          activity_index: activityIndex,
          activity_name: activityName,
          feedback_type: "dislike",
          reason: reason || null,
        },
        {
          onConflict: "itinerary_id,user_id,day_index,activity_index",
        }
      )

    if (feedbackError) {
      console.error("Error submitting feedback:", feedbackError)
      return fail(500, { error: "Failed to submit feedback. Please try again." })
    }

    return { success: true, action: "submitFeedback" }
  },

  removeFeedback: async ({ request, params, locals: { supabase, session } }) => {
    if (!session) {
      return fail(401, { error: "Unauthorized" })
    }

    const { trip_id } = params
    const formData = await request.formData()
    const itineraryId = formData.get("itinerary_id") as string
    const dayIndex = parseInt(formData.get("day_index") as string)
    const activityIndex = parseInt(formData.get("activity_index") as string)

    // Delete the feedback
    const { error: deleteError } = await supabase
      .from("itinerary_feedback")
      .delete()
      .eq("itinerary_id", itineraryId)
      .eq("user_id", session.user.id)
      .eq("day_index", dayIndex)
      .eq("activity_index", activityIndex)

    if (deleteError) {
      console.error("Error removing feedback:", deleteError)
      return fail(500, { error: "Failed to remove feedback. Please try again." })
    }

    return { success: true, action: "removeFeedback" }
  },

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
