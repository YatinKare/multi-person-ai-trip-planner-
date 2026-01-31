import { error } from "@sveltejs/kit"
import type { RequestHandler } from "./$types"
import { createEvents, type EventAttributes, type DateArray } from "ics"
import type { DayItinerary, Activity } from "$lib/types"

export const GET: RequestHandler = async ({
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
    .select("name, status")
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

  // Only allow export for finalized trips
  if (trip.status !== "finalized") {
    throw error(400, "Trip must be finalized before exporting")
  }

  // Load itinerary
  const { data: itinerary, error: itineraryError } = await supabase
    .from("itineraries")
    .select("*")
    .eq("trip_id", trip_id)
    .order("generated_at", { ascending: false })
    .limit(1)
    .maybeSingle()

  if (itineraryError || !itinerary) {
    throw error(404, "No itinerary found for this trip")
  }

  // Parse days from JSONB
  const days: DayItinerary[] = (itinerary.days as unknown as DayItinerary[]) || []
  const destinationName = itinerary.destination_name || "Unknown Destination"

  // Get the earliest date from preferences to calculate actual dates
  const { data: preferences } = await supabase
    .from("preferences")
    .select("dates")
    .eq("trip_id", trip_id)
    .order("submitted_at", { ascending: true })

  // Try to extract a start date from preferences
  let startDate = new Date()
  if (preferences && preferences.length > 0) {
    for (const pref of preferences) {
      const dates = pref.dates as any
      if (dates?.earliest_start) {
        startDate = new Date(dates.earliest_start)
        break
      }
    }
  }

  // Define time slots with their default hours
  const timeSlotHours: Record<string, { start: number; end: number }> = {
    morning: { start: 9, end: 12 },
    afternoon: { start: 13, end: 17 },
    evening: { start: 18, end: 22 },
  }

  // Convert activities to calendar events
  const events: EventAttributes[] = []

  for (let dayIndex = 0; dayIndex < days.length; dayIndex++) {
    const day = days[dayIndex]
    const currentDate = new Date(startDate)
    currentDate.setDate(currentDate.getDate() + dayIndex)

    // Group activities by time slot
    const timeSlots = ["morning", "afternoon", "evening"] as const

    for (const timeSlot of timeSlots) {
      const activities = day.activities.filter((a) => a.time_slot === timeSlot)

      for (const activity of activities) {
        const timeRange = timeSlotHours[timeSlot]
        const eventStartHour = timeRange.start
        const durationHours = activity.duration_hours || (timeRange.end - timeRange.start) / 2

        // Create start and end date arrays for ics library
        const eventStart: DateArray = [
          currentDate.getFullYear(),
          currentDate.getMonth() + 1, // Month is 1-indexed in ics library
          currentDate.getDate(),
          eventStartHour,
          0, // minutes
        ]

        const eventEnd: DateArray = [
          currentDate.getFullYear(),
          currentDate.getMonth() + 1,
          currentDate.getDate(),
          eventStartHour + Math.floor(durationHours),
          Math.round((durationHours % 1) * 60), // Convert fractional hours to minutes
        ]

        // Build event description
        const descriptionParts: string[] = []
        if (activity.description) {
          descriptionParts.push(activity.description)
        }
        if (activity.estimated_cost !== undefined && activity.estimated_cost > 0) {
          descriptionParts.push(`\\nEstimated Cost: $${activity.estimated_cost}`)
        }
        if (activity.tips) {
          descriptionParts.push(`\\nTip: ${activity.tips}`)
        }

        events.push({
          start: eventStart,
          end: eventEnd,
          title: activity.name,
          description: descriptionParts.join(""),
          location: activity.location || destinationName,
          status: "CONFIRMED",
          busyStatus: "BUSY",
          organizer: {
            name: "TripSync",
            email: "noreply@tripsync.com",
          },
          categories: [trip.name, destinationName],
        })
      }
    }
  }

  // Generate .ics file
  const { error: icsError, value: icsContent } = createEvents(events)

  if (icsError || !icsContent) {
    console.error("Error generating .ics file:", icsError)
    throw error(500, "Failed to generate calendar file")
  }

  // Return .ics as response
  return new Response(icsContent, {
    headers: {
      "Content-Type": "text/calendar; charset=utf-8",
      "Content-Disposition": `attachment; filename="${trip.name.replace(/[^a-z0-9]/gi, "_")}_itinerary.ics"`,
    },
  })
}
