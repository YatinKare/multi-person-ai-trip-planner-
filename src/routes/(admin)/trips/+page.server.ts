import type { PageServerLoad, Actions } from "./$types"
import { redirect, fail } from "@sveltejs/kit"

export const load: PageServerLoad = async ({ locals: { supabase, session } }) => {
  if (!session) {
    throw redirect(303, "/login")
  }

  const userId = session.user.id

  // Load trips where user is a member
  const { data: tripMemberships, error: membershipsError } = await supabase
    .from("trip_members")
    .select(`
      trip_id,
      role,
      joined_at,
      trips (
        id,
        name,
        status,
        invite_code,
        rough_timeframe,
        created_at,
        updated_at,
        created_by
      )
    `)
    .eq("user_id", userId)
    .order("joined_at", { ascending: false })

  if (membershipsError) {
    console.error("Error loading trip memberships:", membershipsError)
    return { trips: [], session }
  }

  // Load member counts for each trip
  const tripIds = tripMemberships?.map(m => (m.trips as any)?.id).filter(Boolean) || []

  const { data: memberCounts, error: countsError } = await supabase
    .from("trip_members")
    .select("trip_id, user_id")
    .in("trip_id", tripIds)

  if (countsError) {
    console.error("Error loading member counts:", countsError)
  }

  // Aggregate member counts by trip
  const memberCountsByTrip = (memberCounts || []).reduce((acc, { trip_id }) => {
    acc[trip_id] = (acc[trip_id] || 0) + 1
    return acc
  }, {} as Record<string, number>)

  // Transform and enrich trip data
  const trips = (tripMemberships || [])
    .map(membership => {
      const trip = membership.trips as any
      if (!trip) return null

      return {
        id: trip.id,
        name: trip.name,
        status: trip.status,
        invite_code: trip.invite_code,
        rough_timeframe: trip.rough_timeframe,
        created_at: trip.created_at,
        updated_at: trip.updated_at,
        created_by: trip.created_by,
        role: membership.role,
        member_count: memberCountsByTrip[trip.id] || 1,
        is_organizer: membership.role === "organizer"
      }
    })
    .filter((trip): trip is NonNullable<typeof trip> => trip !== null)

  return {
    trips,
    session
  }
}

export const actions: Actions = {
  createTrip: async ({ locals: { supabase, session }, request }) => {
    if (!session) {
      return fail(401, { error: "Not authenticated" })
    }

    const formData = await request.formData()
    const tripName = formData.get("tripName")?.toString()
    const roughTimeframe = formData.get("roughTimeframe")?.toString() || null

    if (!tripName || tripName.trim().length === 0) {
      return fail(400, { error: "Trip name is required" })
    }

    // Generate a unique invite code using the database function
    // @ts-expect-error - RPC function not in generated types
    const { data: inviteCodeResult, error: inviteCodeError } = await supabase.rpc("generate_invite_code")

    if (inviteCodeError || !inviteCodeResult) {
      console.error("Error generating invite code:", inviteCodeError)
      return fail(500, { error: "Failed to generate invite code" })
    }

    const { data: newTrip, error: tripError } = await supabase
      .from("trips")
      .insert({
        name: tripName.trim(),
        rough_timeframe: roughTimeframe,
        created_by: session.user.id,
        invite_code: inviteCodeResult,
        status: "collecting"
      })
      .select()
      .single()

    if (tripError || !newTrip) {
      console.error("Error creating trip:", tripError)
      return fail(500, { error: "Failed to create trip" })
    }

    // Add creator as organizer in trip_members
    const { error: memberError } = await supabase
      .from("trip_members")
      .insert({
        trip_id: newTrip.id,
        user_id: session.user.id,
        role: "organizer"
      })

    if (memberError) {
      console.error("Error adding trip organizer:", memberError)
      // Clean up the trip if member insert fails
      await supabase.from("trips").delete().eq("id", newTrip.id)
      return fail(500, { error: "Failed to create trip membership" })
    }

    // Return the trip ID and invite code to the client
    return {
      success: true,
      tripId: newTrip.id,
      inviteCode: newTrip.invite_code
    }
  }
}
