import { error } from "@sveltejs/kit"
import type { RequestHandler } from "./$types"
import { jsPDF } from "jspdf"
import type { DayItinerary } from "$lib/types"

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
  const totalCost = itinerary.total_cost || 0
  const destinationName = itinerary.destination_name || "Unknown Destination"

  // Generate PDF
  const doc = new jsPDF()
  const pageWidth = doc.internal.pageSize.getWidth()
  const pageHeight = doc.internal.pageSize.getHeight()
  const margin = 20
  const maxWidth = pageWidth - 2 * margin
  let yPosition = margin

  // Helper function to check if we need a new page
  const checkNewPage = (requiredSpace: number) => {
    if (yPosition + requiredSpace > pageHeight - margin) {
      doc.addPage()
      yPosition = margin
      return true
    }
    return false
  }

  // Helper function to add text with word wrap
  const addWrappedText = (
    text: string,
    x: number,
    y: number,
    maxWidth: number,
    fontSize: number,
    style: "normal" | "bold" = "normal"
  ) => {
    doc.setFontSize(fontSize)
    doc.setFont("helvetica", style)
    const lines = doc.splitTextToSize(text, maxWidth)
    doc.text(lines, x, y)
    return lines.length * (fontSize * 0.35) // Approximate line height
  }

  // Title
  doc.setFontSize(24)
  doc.setFont("helvetica", "bold")
  doc.text(trip.name, margin, yPosition)
  yPosition += 12

  // Destination
  doc.setFontSize(16)
  doc.setFont("helvetica", "normal")
  doc.setTextColor(100, 100, 100)
  doc.text(destinationName, margin, yPosition)
  yPosition += 10

  // Total cost
  doc.setFontSize(14)
  doc.setFont("helvetica", "bold")
  doc.setTextColor(0, 150, 136) // Emerald color
  doc.text(`Total Estimated Cost: $${totalCost.toLocaleString()}`, margin, yPosition)
  yPosition += 15
  doc.setTextColor(0, 0, 0) // Reset to black

  // Itinerary details
  for (const day of days) {
    checkNewPage(30)

    // Day header
    doc.setFillColor(0, 150, 136) // Emerald color
    doc.rect(margin, yPosition - 5, maxWidth, 10, "F")
    doc.setFontSize(14)
    doc.setFont("helvetica", "bold")
    doc.setTextColor(255, 255, 255) // White text
    doc.text(
      `Day ${day.day_number}${day.title ? ": " + day.title : ""}`,
      margin + 5,
      yPosition + 2
    )
    yPosition += 12
    doc.setTextColor(0, 0, 0) // Reset to black

    // Group activities by time slot
    const timeSlots = ["morning", "afternoon", "evening"]
    const timeSlotLabels: Record<string, string> = {
      morning: "Morning",
      afternoon: "Afternoon",
      evening: "Evening",
    }

    for (const timeSlot of timeSlots) {
      const activities = day.activities.filter((a) => a.time_slot === timeSlot)

      if (activities.length === 0) continue

      checkNewPage(20)

      // Time slot header
      doc.setFontSize(12)
      doc.setFont("helvetica", "bold")
      doc.text(timeSlotLabels[timeSlot] || timeSlot, margin, yPosition)
      yPosition += 7

      for (const activity of activities) {
        checkNewPage(35)

        // Activity name
        doc.setFontSize(11)
        doc.setFont("helvetica", "bold")
        const nameHeight = addWrappedText(
          activity.name,
          margin + 5,
          yPosition,
          maxWidth - 5,
          11,
          "bold"
        )
        yPosition += nameHeight + 2

        // Activity description
        doc.setFontSize(9)
        doc.setFont("helvetica", "normal")
        if (activity.description) {
          const descHeight = addWrappedText(
            activity.description,
            margin + 5,
            yPosition,
            maxWidth - 5,
            9
          )
          yPosition += descHeight + 2
        }

        // Activity details (location, cost, duration)
        doc.setFontSize(9)
        doc.setTextColor(100, 100, 100)
        const details: string[] = []
        if (activity.location) {
          details.push(`Location: ${activity.location}`)
        }
        if (activity.estimated_cost !== undefined && activity.estimated_cost > 0) {
          details.push(`Cost: $${activity.estimated_cost}`)
        }
        if (activity.duration_hours) {
          details.push(`Duration: ${activity.duration_hours}h`)
        }
        if (details.length > 0) {
          const detailsHeight = addWrappedText(
            details.join(" • "),
            margin + 5,
            yPosition,
            maxWidth - 5,
            9
          )
          yPosition += detailsHeight + 2
        }
        doc.setTextColor(0, 0, 0) // Reset to black

        // Tips (if available)
        if (activity.tips) {
          doc.setFontSize(8)
          doc.setTextColor(0, 150, 136)
          doc.setFont("helvetica", "italic")
          const tipsHeight = addWrappedText(
            `💡 ${activity.tips}`,
            margin + 5,
            yPosition,
            maxWidth - 5,
            8
          )
          yPosition += tipsHeight + 2
          doc.setTextColor(0, 0, 0)
        }

        yPosition += 5 // Space between activities
      }

      yPosition += 3 // Space between time slots
    }

    // Day total cost
    doc.setFontSize(10)
    doc.setFont("helvetica", "bold")
    doc.setTextColor(0, 150, 136)
    doc.text(
      `Day ${day.day_number} Total: $${day.total_cost.toLocaleString()}`,
      margin,
      yPosition
    )
    doc.setTextColor(0, 0, 0)
    yPosition += 12
  }

  // Footer on last page
  checkNewPage(15)
  doc.setFontSize(8)
  doc.setFont("helvetica", "italic")
  doc.setTextColor(150, 150, 150)
  doc.text("Generated by TripSync", margin, yPosition)
  doc.text(
    new Date().toLocaleDateString(),
    pageWidth - margin,
    yPosition,
    { align: "right" }
  )

  // Generate PDF as buffer
  const pdfBuffer = doc.output("arraybuffer")

  // Return PDF as response
  return new Response(pdfBuffer, {
    headers: {
      "Content-Type": "application/pdf",
      "Content-Disposition": `attachment; filename="${trip.name.replace(/[^a-z0-9]/gi, "_")}_itinerary.pdf"`,
    },
  })
}
