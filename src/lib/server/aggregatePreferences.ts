import type { Database } from "../../DatabaseDefinitions"

type Preference = Database["public"]["Tables"]["preferences"]["Row"]

export interface AggregatedPreferences {
  dates: {
    earliestCommonStart: string | null
    latestCommonEnd: string | null
    commonWindow: { start: string; end: string } | null
    idealDurations: string[]
  }
  budget: {
    minBudget: number
    maxBudget: number
    commonInclusions: string[]
    flexibilityLevels: Record<string, number>
  }
  destination: {
    commonVibes: string[]
    allVibes: string[]
    popularScopes: Record<string, number>
    specificPlaces: string[]
    placesToAvoid: string[]
  }
  constraints: {
    dietary: string[]
    accessibility: string[]
    hardNos: string[]
  }
  conflicts: {
    hasConflicts: boolean
    noDateOverlap: boolean
    noBudgetOverlap: boolean
    noCommonVibes: boolean
    details: string[]
  }
}

export function aggregatePreferences(preferences: Preference[]): AggregatedPreferences {
  // Handle empty case
  if (preferences.length === 0) {
    return {
      dates: {
        earliestCommonStart: null,
        latestCommonEnd: null,
        commonWindow: null,
        idealDurations: []
      },
      budget: {
        minBudget: 0,
        maxBudget: 0,
        commonInclusions: [],
        flexibilityLevels: {}
      },
      destination: {
        commonVibes: [],
        allVibes: [],
        popularScopes: {},
        specificPlaces: [],
        placesToAvoid: []
      },
      constraints: {
        dietary: [],
        accessibility: [],
        hardNos: []
      },
      conflicts: {
        hasConflicts: false,
        noDateOverlap: false,
        noBudgetOverlap: false,
        noCommonVibes: false,
        details: []
      }
    }
  }

  // Parse all dates
  const allDates = preferences.map(p => {
    const dates = p.dates as any
    return {
      earliestStart: dates?.earliestStart ? new Date(dates.earliestStart) : null,
      latestEnd: dates?.latestEnd ? new Date(dates.latestEnd) : null,
      idealDuration: dates?.idealDuration || null,
      flexible: dates?.flexible || false
    }
  }).filter(d => d.earliestStart && d.latestEnd)

  // Find date overlap (common window)
  let commonStart: Date | null = null
  let commonEnd: Date | null = null

  if (allDates.length > 0) {
    // Latest of all earliest starts
    commonStart = new Date(Math.max(...allDates.map(d => d.earliestStart!.getTime())))
    // Earliest of all latest ends
    commonEnd = new Date(Math.min(...allDates.map(d => d.latestEnd!.getTime())))
  }

  const hasDateOverlap = commonStart && commonEnd && commonStart <= commonEnd
  const idealDurations = [...new Set(allDates.map(d => d.idealDuration).filter(Boolean))]

  // Parse all budgets
  const allBudgets = preferences.map(p => {
    const budget = p.budget as any
    return {
      min: budget?.min || 0,
      max: budget?.max || 0,
      includeFlights: budget?.includeFlights || false,
      includeAccommodation: budget?.includeAccommodation || false,
      includeFood: budget?.includeFood || false,
      includeActivities: budget?.includeActivities || false,
      flexibility: budget?.flexibility || "prefer_under"
    }
  })

  // Find budget overlap
  const minOfMaxBudgets = Math.min(...allBudgets.map(b => b.max))
  const maxOfMinBudgets = Math.max(...allBudgets.map(b => b.min))
  const hasBudgetOverlap = maxOfMinBudgets <= minOfMaxBudgets

  // Find common budget inclusions (all must include for it to be common)
  const commonInclusions = []
  if (allBudgets.every(b => b.includeFlights)) commonInclusions.push("Flights")
  if (allBudgets.every(b => b.includeAccommodation)) commonInclusions.push("Accommodation")
  if (allBudgets.every(b => b.includeFood)) commonInclusions.push("Food")
  if (allBudgets.every(b => b.includeActivities)) commonInclusions.push("Activities")

  // Count flexibility levels
  const flexibilityLevels: Record<string, number> = {}
  allBudgets.forEach(b => {
    flexibilityLevels[b.flexibility] = (flexibilityLevels[b.flexibility] || 0) + 1
  })

  // Parse all destination preferences
  const allDestPrefs = preferences.map(p => {
    const destPrefs = p.destination_prefs as any
    return {
      vibes: destPrefs?.vibes || [],
      scope: destPrefs?.scope || "either",
      specificPlaces: destPrefs?.specificPlaces || "",
      placesToAvoid: destPrefs?.placesToAvoid || ""
    }
  })

  // Find common vibes (intersection)
  let commonVibes: string[] = []
  if (allDestPrefs.length > 0) {
    commonVibes = allDestPrefs[0].vibes.filter((vibe: string) =>
      allDestPrefs.every(pref => pref.vibes.includes(vibe))
    )
  }

  // All vibes (union)
  const allVibesSet = new Set<string>()
  allDestPrefs.forEach(pref => {
    pref.vibes.forEach((vibe: string) => allVibesSet.add(vibe))
  })
  const allVibes = Array.from(allVibesSet)

  // Count travel scope preferences
  const popularScopes: Record<string, number> = {}
  allDestPrefs.forEach(pref => {
    popularScopes[pref.scope] = (popularScopes[pref.scope] || 0) + 1
  })

  // Collect specific places and places to avoid
  const specificPlaces = allDestPrefs
    .map(pref => pref.specificPlaces)
    .filter(Boolean)
  const placesToAvoid = allDestPrefs
    .map(pref => pref.placesToAvoid)
    .filter(Boolean)

  // Parse all constraints
  const allConstraints = preferences.map(p => {
    const constraints = p.constraints as any
    return {
      dietary: constraints?.dietary || [],
      otherDietary: constraints?.otherDietary || "",
      accessibility: constraints?.accessibility || [],
      otherAccessibility: constraints?.otherAccessibility || "",
      hardNos: constraints?.hardNos || ""
    }
  })

  // Collect all dietary restrictions (union)
  const dietarySet = new Set<string>()
  allConstraints.forEach(c => {
    c.dietary.forEach((d: string) => dietarySet.add(d))
    if (c.otherDietary) dietarySet.add(c.otherDietary)
  })
  const dietary = Array.from(dietarySet)

  // Collect all accessibility needs (union)
  const accessibilitySet = new Set<string>()
  allConstraints.forEach(c => {
    c.accessibility.forEach((a: string) => accessibilitySet.add(a))
    if (c.otherAccessibility) accessibilitySet.add(c.otherAccessibility)
  })
  const accessibility = Array.from(accessibilitySet)

  // Collect all hard no's
  const hardNos = allConstraints
    .map(c => c.hardNos)
    .filter(Boolean)

  // Detect conflicts
  const conflicts = {
    hasConflicts: false,
    noDateOverlap: !hasDateOverlap && allDates.length > 0,
    noBudgetOverlap: !hasBudgetOverlap && allBudgets.length > 0,
    noCommonVibes: commonVibes.length === 0 && allVibes.length > 0,
    details: [] as string[]
  }

  if (conflicts.noDateOverlap) {
    conflicts.details.push("No overlapping dates between all members")
  }
  if (conflicts.noBudgetOverlap) {
    conflicts.details.push("Budget ranges don't overlap")
  }
  if (conflicts.noCommonVibes) {
    conflicts.details.push("No common vibes selected by all members")
  }

  conflicts.hasConflicts = conflicts.details.length > 0

  return {
    dates: {
      earliestCommonStart: commonStart ? commonStart.toISOString().split('T')[0] : null,
      latestCommonEnd: commonEnd ? commonEnd.toISOString().split('T')[0] : null,
      commonWindow: hasDateOverlap && commonStart && commonEnd
        ? { start: commonStart.toISOString().split('T')[0], end: commonEnd.toISOString().split('T')[0] }
        : null,
      idealDurations
    },
    budget: {
      minBudget: maxOfMinBudgets,
      maxBudget: minOfMaxBudgets,
      commonInclusions,
      flexibilityLevels
    },
    destination: {
      commonVibes,
      allVibes,
      popularScopes,
      specificPlaces,
      placesToAvoid
    },
    constraints: {
      dietary,
      accessibility,
      hardNos
    },
    conflicts
  }
}
