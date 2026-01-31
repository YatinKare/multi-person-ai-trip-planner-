import { error, fail } from "@sveltejs/kit"
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
  const memberUserIds = members?.map((m) => m.user_id) || []
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

  const userIdsWithPrefs = new Set(preferencesData?.map((p) => p.user_id) || [])
  const profilesMap = new Map(profiles?.map((p) => [p.id, p]) || [])

  // Combine member data with preference status
  const membersWithStatus =
    members?.map((member) => {
      const profile = profilesMap.get(member.user_id)
      return {
        user_id: member.user_id,
        role: member.role,
        full_name: profile?.full_name || null,
        avatar_url: profile?.avatar_url || null,
        has_preferences: userIdsWithPrefs.has(member.user_id),
      }
    }) || []

  // Load votes for this recommendation (if recommendations exist)
  let votes: any[] = []
  let userVotes: Record<number, string> = {}

  if (recommendations) {
    const { data: votesData, error: votesError } = await supabase
      .from("destination_votes")
      .select("*")
      .eq("recommendation_id", recommendations.id)

    if (votesError) {
      console.error("Error loading votes:", votesError)
    } else {
      votes = votesData || []
      // Create a map of destination_index -> vote_type for current user
      userVotes = votes
        .filter((v) => v.user_id === session.user.id)
        .reduce(
          (acc, v) => {
            acc[v.destination_index] = v.vote_type
            return acc
          },
          {} as Record<number, string>,
        )
    }
  }

  // Calculate vote counts per destination
  const voteCounts: Record<
    number,
    { upvotes: number; downvotes: number }
  > = {}
  votes.forEach((vote) => {
    if (!voteCounts[vote.destination_index]) {
      voteCounts[vote.destination_index] = { upvotes: 0, downvotes: 0 }
    }
    if (vote.vote_type === "upvote") {
      voteCounts[vote.destination_index].upvotes++
    } else if (vote.vote_type === "downvote") {
      voteCounts[vote.destination_index].downvotes++
    }
  })

  return {
    trip,
    recommendations: recommendations || null,
    userRole: membership.role,
    members: membersWithStatus,
    voteCounts,
    userVotes,
    session,
  }
}

export const actions: Actions = {
  selectDestination: async ({ request, params, locals: { supabase, session } }) => {
    if (!session) {
      return fail(401, { message: "Unauthorized" })
    }

    const { trip_id } = params
    const formData = await request.formData()
    const destinationIndex = parseInt(formData.get("destinationIndex") as string)

    if (isNaN(destinationIndex)) {
      return fail(400, { message: "Invalid destination index" })
    }

    // Verify user is an organizer of this trip
    const { data: membership } = await supabase
      .from("trip_members")
      .select("role")
      .eq("trip_id", trip_id)
      .eq("user_id", session.user.id)
      .single()

    if (!membership || membership.role !== "organizer") {
      return fail(403, { message: "Only organizers can select destinations" })
    }

    // Get the current recommendations
    const { data: recommendations, error: recsError } = await supabase
      .from("recommendations")
      .select("*")
      .eq("trip_id", trip_id)
      .order("generated_at", { ascending: false })
      .limit(1)
      .single()

    if (recsError || !recommendations) {
      return fail(404, { message: "No recommendations found" })
    }

    // Validate that the destination index is valid
    const destinations = recommendations.destinations as any[]
    if (destinationIndex < 0 || destinationIndex >= destinations.length) {
      return fail(400, { message: "Invalid destination index" })
    }

    // Update the recommendations table with selected destination
    const { error: updateRecsError } = await supabase
      .from("recommendations")
      .update({
        selected_destination_index: destinationIndex,
        selected_at: new Date().toISOString(),
        selected_by: session.user.id,
      })
      .eq("id", recommendations.id)

    if (updateRecsError) {
      console.error("Error updating recommendations:", updateRecsError)
      return fail(500, { message: "Failed to select destination" })
    }

    // Update trip status to 'planning'
    const { error: updateTripError } = await supabase
      .from("trips")
      .update({ status: "planning" })
      .eq("id", trip_id)

    if (updateTripError) {
      console.error("Error updating trip status:", updateTripError)
      return fail(500, { message: "Failed to update trip status" })
    }

    return { success: true }
  },

  vote: async ({ request, params, locals: { supabase, session } }) => {
    if (!session) {
      return fail(401, { error: "Unauthorized" })
    }

    const { trip_id } = params
    const formData = await request.formData()
    const destinationIndex = parseInt(formData.get("destination_index") as string)
    const voteType = formData.get("vote_type") as "upvote" | "downvote"
    const recommendationId = formData.get("recommendation_id") as string

    if (!recommendationId || isNaN(destinationIndex) || !voteType) {
      return fail(400, { error: "Invalid vote data" })
    }

    // Verify user is a member of this trip
    const { data: membership } = await supabase
      .from("trip_members")
      .select("role")
      .eq("trip_id", trip_id)
      .eq("user_id", session.user.id)
      .single()

    if (!membership) {
      return fail(403, { error: "Not a member of this trip" })
    }

    // Check if user already has a vote for this destination
    const { data: existingVote } = await supabase
      .from("destination_votes")
      .select("*")
      .eq("recommendation_id", recommendationId)
      .eq("user_id", session.user.id)
      .eq("destination_index", destinationIndex)
      .maybeSingle()

    if (existingVote) {
      // If same vote type, remove the vote (toggle off)
      if (existingVote.vote_type === voteType) {
        const { error: deleteError } = await supabase
          .from("destination_votes")
          .delete()
          .eq("id", existingVote.id)

        if (deleteError) {
          console.error("Error removing vote:", deleteError)
          return fail(500, { error: "Failed to remove vote" })
        }

        return { success: true, action: "removed" }
      } else {
        // Different vote type, update the vote
        const { error: updateError } = await supabase
          .from("destination_votes")
          .update({ vote_type: voteType })
          .eq("id", existingVote.id)

        if (updateError) {
          console.error("Error updating vote:", updateError)
          return fail(500, { error: "Failed to update vote" })
        }

        return { success: true, action: "updated" }
      }
    } else {
      // No existing vote, insert new one
      const { error: insertError } = await supabase
        .from("destination_votes")
        .insert({
          recommendation_id: recommendationId,
          user_id: session.user.id,
          destination_index: destinationIndex,
          vote_type: voteType,
        })

      if (insertError) {
        console.error("Error inserting vote:", insertError)
        return fail(500, { error: "Failed to add vote" })
      }

      return { success: true, action: "added" }
    }
  },
}
