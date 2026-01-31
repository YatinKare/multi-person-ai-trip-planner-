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

  // Load activity suggestions for this trip
  const { data: suggestions, error: suggestionsError } = await supabase
    .from("activity_suggestions")
    .select("*")
    .eq("trip_id", trip_id)
    .order("created_at", { ascending: false })

  if (suggestionsError) {
    console.error("Error loading suggestions:", suggestionsError)
  }

  // Load user profiles for suggestions
  const suggestionUserIds = suggestions?.map(s => s.user_id) || []
  const { data: suggestionProfiles } = await supabase
    .from("profiles")
    .select("id, full_name")
    .in("id", suggestionUserIds)

  // Attach profiles to suggestions
  const suggestionsWithProfiles = suggestions?.map(s => ({
    ...s,
    user_name: suggestionProfiles?.find(p => p.id === s.user_id)?.full_name || "Unknown"
  })) || []

  return {
    trip,
    itinerary,
    userRole: membership.role,
    members: members || [],
    userId: session.user.id,
    feedback: feedback || [],
    userFeedback: userFeedback || [],
    suggestions: suggestionsWithProfiles,
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

  suggestActivity: async ({ request, params, locals: { supabase, session } }) => {
    if (!session) {
      return fail(401, { error: "Unauthorized", action: "suggestActivity" })
    }

    const { trip_id } = params
    const formData = await request.formData()
    const dayIndex = parseInt(formData.get("dayIndex") as string)
    const timeSlot = formData.get("timeSlot") as string
    const activityName = formData.get("activityName") as string
    const activityDescription = formData.get("activityDescription") as string | null
    const estimatedCostStr = formData.get("estimatedCost") as string
    const estimatedCost = estimatedCostStr ? parseFloat(estimatedCostStr) : null
    const location = formData.get("location") as string | null
    const reason = formData.get("reason") as string | null

    // Validate required fields
    if (!activityName || !timeSlot || dayIndex < 0) {
      return fail(400, { error: "Missing required fields", action: "suggestActivity" })
    }

    // Check if user is a member of this trip
    const { data: membership, error: membershipError } = await supabase
      .from("trip_members")
      .select("role")
      .eq("trip_id", trip_id)
      .eq("user_id", session.user.id)
      .single()

    if (membershipError || !membership) {
      return fail(403, { error: "You are not a member of this trip", action: "suggestActivity" })
    }

    // Check if trip is finalized (no suggestions allowed after finalization)
    const { data: trip, error: tripError } = await supabase
      .from("trips")
      .select("status")
      .eq("id", trip_id)
      .single()

    if (tripError || !trip) {
      return fail(404, { error: "Trip not found", action: "suggestActivity" })
    }

    if (trip.status === "finalized") {
      return fail(403, { error: "Cannot suggest activities on finalized trips", action: "suggestActivity" })
    }

    // Insert the suggestion
    const { error: suggestionError } = await supabase
      .from("activity_suggestions")
      .insert({
        trip_id: trip_id,
        user_id: session.user.id,
        day_index: dayIndex,
        time_slot: timeSlot,
        activity_name: activityName,
        activity_description: activityDescription || null,
        estimated_cost: estimatedCost,
        location: location || null,
        reason: reason || null,
        status: "pending",
      })

    if (suggestionError) {
      console.error("Error submitting suggestion:", suggestionError)
      return fail(500, { error: "Failed to submit suggestion. Please try again.", action: "suggestActivity" })
    }

    return { success: true, action: "suggestActivity" }
  },

  acceptSuggestion: async ({ request, params, locals: { supabase, session } }) => {
    if (!session) {
      return fail(401, { error: "Unauthorized", action: "acceptSuggestion" })
    }

    const { trip_id } = params
    const formData = await request.formData()
    const suggestionId = formData.get("suggestionId") as string

    // Check if user is the organizer
    const { data: membership, error: membershipError } = await supabase
      .from("trip_members")
      .select("role")
      .eq("trip_id", trip_id)
      .eq("user_id", session.user.id)
      .single()

    if (membershipError || !membership) {
      return fail(403, { error: "You are not a member of this trip", action: "acceptSuggestion" })
    }

    if (membership.role !== "organizer") {
      return fail(403, { error: "Only the organizer can review suggestions", action: "acceptSuggestion" })
    }

    // Update suggestion status
    const { error: updateError } = await supabase
      .from("activity_suggestions")
      .update({
        status: "accepted",
        reviewed_by: session.user.id,
        reviewed_at: new Date().toISOString(),
      })
      .eq("id", suggestionId)
      .eq("trip_id", trip_id)

    if (updateError) {
      console.error("Error accepting suggestion:", updateError)
      return fail(500, { error: "Failed to accept suggestion. Please try again.", action: "acceptSuggestion" })
    }

    return { success: true, action: "acceptSuggestion" }
  },

  rejectSuggestion: async ({ request, params, locals: { supabase, session } }) => {
    if (!session) {
      return fail(401, { error: "Unauthorized", action: "rejectSuggestion" })
    }

    const { trip_id } = params
    const formData = await request.formData()
    const suggestionId = formData.get("suggestionId") as string

    // Check if user is the organizer
    const { data: membership, error: membershipError } = await supabase
      .from("trip_members")
      .select("role")
      .eq("trip_id", trip_id)
      .eq("user_id", session.user.id)
      .single()

    if (membershipError || !membership) {
      return fail(403, { error: "You are not a member of this trip", action: "rejectSuggestion" })
    }

    if (membership.role !== "organizer") {
      return fail(403, { error: "Only the organizer can review suggestions", action: "rejectSuggestion" })
    }

    // Update suggestion status
    const { error: updateError } = await supabase
      .from("activity_suggestions")
      .update({
        status: "rejected",
        reviewed_by: session.user.id,
        reviewed_at: new Date().toISOString(),
      })
      .eq("id", suggestionId)
      .eq("trip_id", trip_id)

    if (updateError) {
      console.error("Error rejecting suggestion:", updateError)
      return fail(500, { error: "Failed to reject suggestion. Please try again.", action: "rejectSuggestion" })
    }

    return { success: true, action: "rejectSuggestion" }
  },

  regenerate: async ({ request, params, locals: { supabase, session }, fetch }) => {
    if (!session) {
      return fail(401, { error: "Unauthorized", action: "regenerate" })
    }

    const { trip_id } = params
    const formData = await request.formData()
    const feedback = formData.get("feedback") as string
    const regenerationCount = parseInt(formData.get("regeneration_count") as string) || 0

    // Validate feedback
    if (!feedback || feedback.trim().length < 10) {
      return fail(400, { error: "Feedback must be at least 10 characters", action: "regenerate" })
    }

    if (feedback.length > 1000) {
      return fail(400, { error: "Feedback must be 1000 characters or less", action: "regenerate" })
    }

    // Check max regenerations
    const maxRegenerations = 5
    if (regenerationCount >= maxRegenerations) {
      return fail(400, { error: "Maximum regenerations reached (5)", action: "regenerate" })
    }

    // Check if user is the organizer
    const { data: membership, error: membershipError } = await supabase
      .from("trip_members")
      .select("role")
      .eq("trip_id", trip_id)
      .eq("user_id", session.user.id)
      .single()

    if (membershipError || !membership) {
      return fail(403, { error: "You are not a member of this trip", action: "regenerate" })
    }

    if (membership.role !== "organizer") {
      return fail(403, { error: "Only the organizer can regenerate the itinerary", action: "regenerate" })
    }

    // Check trip status
    const { data: trip, error: tripError } = await supabase
      .from("trips")
      .select("status")
      .eq("id", trip_id)
      .single()

    if (tripError || !trip) {
      return fail(404, { error: "Trip not found", action: "regenerate" })
    }

    if (trip.status !== "planning") {
      return fail(400, { error: "Can only regenerate itinerary in 'planning' status", action: "regenerate" })
    }

    try {
      // Call FastAPI backend to regenerate itinerary
      const response = await fetch("http://localhost:8000/api/ai/itinerary/regenerate", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${session.access_token}`,
        },
        body: JSON.stringify({
          trip_id: trip_id,
          feedback: feedback.trim(),
          regeneration_count: regenerationCount,
        }),
      })

      if (!response.ok) {
        const error = await response.json().catch(() => ({}))
        console.error("Error from API:", error)
        return fail(response.status, {
          error: error.detail || "Failed to regenerate itinerary. Please try again.",
          action: "regenerate",
        })
      }

      const result = await response.json()

      // Update the itinerary in the database with the new data
      const { error: updateError } = await supabase
        .from("itineraries")
        .update({
          days: result.days,
          total_cost: result.total_cost,
          generated_at: result.generated_at,
          regeneration_count: regenerationCount + 1,
        })
        .eq("trip_id", trip_id)

      if (updateError) {
        console.error("Error updating itinerary:", updateError)
        return fail(500, {
          error: "Failed to save regenerated itinerary. Please try again.",
          action: "regenerate",
        })
      }

      return { success: true, action: "regenerate" }
    } catch (err) {
      console.error("Error regenerating itinerary:", err)
      return fail(500, {
        error: err instanceof Error ? err.message : "Failed to regenerate itinerary. Please try again.",
        action: "regenerate",
      })
    }
  },
}
