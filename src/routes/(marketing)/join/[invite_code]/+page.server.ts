import type { PageServerLoad, Actions } from "./$types"
import { redirect, fail } from "@sveltejs/kit"

export const load: PageServerLoad = async ({
  params,
  locals: { supabaseServiceRole, session },
}) => {
  const { invite_code } = params

  // Use service role to bypass RLS - allows unauthenticated users to view trip info
  const { data: trip, error: tripError } = await supabaseServiceRole
    .from("trips")
    .select(
      `
      id,
      name,
      status,
      invite_code,
      rough_timeframe,
      created_by,
      created_at
    `,
    )
    .eq("invite_code", invite_code)
    .single()

  if (tripError || !trip) {
    console.error("Error loading trip by invite code:", tripError)
    return {
      trip: null,
      error: "Invalid or expired invite link",
      session,
    }
  }

  // Load organizer profile (service role to bypass RLS)
  const { data: organizerProfile } = await supabaseServiceRole
    .from("profiles")
    .select("id, full_name, avatar_url")
    .eq("id", trip.created_by)
    .single()

  // If user is authenticated, check if they're already a member
  let isAlreadyMember = false
  let memberCount = 0
  let otherMembers: Array<{
    full_name: string | null
    avatar_url: string | null
  }> = []

  if (session) {
    const { data: membership } = await supabaseServiceRole
      .from("trip_members")
      .select("trip_id")
      .eq("trip_id", trip.id)
      .eq("user_id", session.user.id)
      .single()

    isAlreadyMember = !!membership

    // If already a member, redirect to trip dashboard
    if (isAlreadyMember) {
      throw redirect(303, `/trips/${trip.id}`)
    }
  }

  // Load member count and some members for social proof (service role to bypass RLS)
  const { data: members } = await supabaseServiceRole
    .from("trip_members")
    .select(
      `
      user_id,
      profiles (
        full_name,
        avatar_url
      )
    `,
    )
    .eq("trip_id", trip.id)
    .limit(3)

  memberCount = members?.length || 0
  otherMembers = (members || [])
    .map(
      (m) =>
        m.profiles as unknown as {
          full_name: string | null
          avatar_url: string | null
        },
    )
    .filter(Boolean)
    .slice(0, 3)

  return {
    trip: {
      id: trip.id,
      name: trip.name,
      status: trip.status,
      invite_code: trip.invite_code,
      rough_timeframe: trip.rough_timeframe,
      created_by: trip.created_by,
      created_at: trip.created_at,
      organizer: organizerProfile,
    },
    memberCount,
    otherMembers,
    isAlreadyMember,
    session,
    error: null,
  }
}

export const actions: Actions = {
  joinTrip: async ({
    params,
    locals: { supabase, supabaseServiceRole, session },
  }) => {
    if (!session) {
      // Redirect to login with return URL
      const returnUrl = `/join/${params.invite_code}`
      throw redirect(303, `/login?redirectTo=${encodeURIComponent(returnUrl)}`)
    }

    const { invite_code } = params

    // Load trip by invite code (service role to bypass RLS)
    const { data: trip, error: tripError } = await supabaseServiceRole
      .from("trips")
      .select("id, status")
      .eq("invite_code", invite_code)
      .single()

    if (tripError || !trip) {
      return fail(404, { error: "Trip not found" })
    }

    // Check if user is already a member
    const { data: existingMembership } = await supabaseServiceRole
      .from("trip_members")
      .select("trip_id")
      .eq("trip_id", trip.id)
      .eq("user_id", session.user.id)
      .single()

    if (existingMembership) {
      // Already a member, just redirect
      throw redirect(303, `/trips/${trip.id}`)
    }

    // Add user as member (use regular client - RLS will verify auth)
    const { error: memberError } = await supabase.from("trip_members").insert({
      trip_id: trip.id,
      user_id: session.user.id,
      role: "member",
    })

    if (memberError) {
      console.error("Error adding trip member:", memberError)
      return fail(500, { error: "Failed to join trip" })
    }

    // Redirect to preference form
    throw redirect(303, `/trips/${trip.id}/preferences`)
  },
}
