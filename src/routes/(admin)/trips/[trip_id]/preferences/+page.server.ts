import { error, redirect, fail } from "@sveltejs/kit"
import type { PageServerLoad, Actions } from "./$types"

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

  // Load user's existing preferences if they exist
  const { data: existingPreferences, error: preferencesError } = await supabase
    .from("preferences")
    .select("*")
    .eq("trip_id", trip_id)
    .eq("user_id", session.user.id)
    .single()

  // It's OK if preferences don't exist yet (user hasn't submitted)
  if (preferencesError && preferencesError.code !== "PGRST116") {
    console.error("Error loading preferences:", preferencesError)
  }

  return {
    trip,
    existingPreferences: existingPreferences || null,
    userRole: membership.role,
    session
  }
}

export const actions: Actions = {
  submitPreferences: async ({ request, params, locals: { supabase, session } }) => {
    if (!session) {
      return fail(401, { message: "Unauthorized" })
    }

    const { trip_id } = params
    const formData = await request.formData()

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

    // Parse form data
    const earliestStartDate = formData.get("earliestStartDate") as string
    const latestEndDate = formData.get("latestEndDate") as string
    const tripDuration = formData.get("tripDuration") as string
    const flexibleDates = formData.get("flexibleDates") === "true"

    const budgetMin = parseInt(formData.get("budgetMin") as string)
    const budgetMax = parseInt(formData.get("budgetMax") as string)
    const includeFlights = formData.get("includeFlights") === "true"
    const includeAccommodation = formData.get("includeAccommodation") === "true"
    const includeFood = formData.get("includeFood") === "true"
    const includeActivities = formData.get("includeActivities") === "true"
    const budgetFlexibility = formData.get("budgetFlexibility") as string

    const selectedVibes = JSON.parse(formData.get("selectedVibes") as string)
    const travelScope = formData.get("travelScope") as string
    const specificPlaces = formData.get("specificPlaces") as string
    const placesToAvoid = formData.get("placesToAvoid") as string

    const selectedDietary = JSON.parse(formData.get("selectedDietary") as string)
    const otherDietary = formData.get("otherDietary") as string
    const selectedAccessibility = JSON.parse(formData.get("selectedAccessibility") as string)
    const otherAccessibility = formData.get("otherAccessibility") as string
    const hardNos = formData.get("hardNos") as string

    const additionalNotes = formData.get("additionalNotes") as string

    // Validate required fields
    if (!earliestStartDate || !latestEndDate || !tripDuration) {
      return fail(400, { message: "Please fill in all required date fields" })
    }

    if (selectedVibes.length === 0) {
      return fail(400, { message: "Please select at least one vibe" })
    }

    // Build preference objects
    const datesPrefs = {
      earliestStart: earliestStartDate,
      latestEnd: latestEndDate,
      idealDuration: tripDuration,
      flexible: flexibleDates
    }

    const budgetPrefs = {
      min: budgetMin,
      max: budgetMax,
      includeFlights,
      includeAccommodation,
      includeFood,
      includeActivities,
      flexibility: budgetFlexibility
    }

    const destinationPrefs = {
      vibes: selectedVibes,
      scope: travelScope,
      specificPlaces: specificPlaces || null,
      placesToAvoid: placesToAvoid || null
    }

    const constraintsPrefs = {
      dietary: selectedDietary,
      otherDietary: otherDietary || null,
      accessibility: selectedAccessibility,
      otherAccessibility: otherAccessibility || null,
      hardNos: hardNos || null
    }

    // Check if preferences already exist
    const { data: existingPrefs, error: checkError } = await supabase
      .from("preferences")
      .select("id")
      .eq("trip_id", trip_id)
      .eq("user_id", session.user.id)
      .single()

    let result

    if (existingPrefs) {
      // Update existing preferences
      const { error: updateError } = await supabase
        .from("preferences")
        .update({
          dates: datesPrefs,
          budget: budgetPrefs,
          destination_prefs: destinationPrefs,
          constraints: constraintsPrefs,
          notes: additionalNotes || null,
          updated_at: new Date().toISOString()
        })
        .eq("id", existingPrefs.id)

      if (updateError) {
        console.error("Error updating preferences:", updateError)
        return fail(500, { message: "Failed to save preferences. Please try again." })
      }
    } else {
      // Insert new preferences
      const { error: insertError } = await supabase
        .from("preferences")
        .insert({
          trip_id,
          user_id: session.user.id,
          dates: datesPrefs,
          budget: budgetPrefs,
          destination_prefs: destinationPrefs,
          constraints: constraintsPrefs,
          notes: additionalNotes || null,
          submitted_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        })

      if (insertError) {
        console.error("Error inserting preferences:", insertError)
        return fail(500, { message: "Failed to save preferences. Please try again." })
      }
    }

    // Redirect back to trip dashboard
    throw redirect(303, `/trips/${trip_id}`)
  }
}
