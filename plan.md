#TripSync - AI-Powered Group Trip Planning

## Goal
Build a web application that eliminates group trip planning chaos by collecting structured preferences from all participants and using AI to generate destination recommendations and full itineraries based on the group's aggregated constraints.

## Current State
System has set up the basic project structure for supabase and 

## Problem Statement
- No structure for collecting preferences
- No automated aggregation of constraints
- No visibility into group compatibility (date overlaps, budget ranges)
- Decision paralysis when no one wants to "lead the effort"
- Async responses with no clear format

## User Personas

### The Initiator
- Wants the trip to happen
- Willing to create the trip but doesn't want to chase everyone
- Needs: easy invite flow, visibility into who's responded, ability to move forward

### The "Whatever" Person
- Genuinely flexible, will go on the trip
- Doesn't want to make decisions
- Needs: guided input so flexibility becomes useful data

### The Constraint Person
- Has real restrictions (budget, dates, accessibility, dietary)
- Needs: structured way to express constraints that won't be forgotten

---

## Requirements

### P0 - MVP (Must Ship)

#### Authentication & User Management
- [ ] Google OAuth sign-in (via Supabase Auth from CMSaasStarter template)
- [ ] User profile with display name and email
- [ ] Users can be members of multiple trips

#### Trip Creation & Invites
- [ ] Initiator can create a new trip with a name
- [ ] System generates unique invite code/link for each trip
- [ ] Invite link is shareable (copy to clipboard)
- [ ] Anyone with link can join trip after authenticating
- [ ] Creator becomes trip "organizer" with elevated permissions

#### Preference Collection Form
- [ ] Each member fills out structured preference form per trip
- [ ] Form fields:
  - **Dates**
    - [ ] Earliest start date (date picker)
    - [ ] Latest end date (date picker)
    - [ ] Ideal trip length (dropdown: "2-3 days", "4-5 days", "1 week", "1+ week", "flexible")
    - [ ] Flexibility toggle ("I can adjust if needed")
  - **Budget**
    - [ ] Budget range slider ($0 - $3000+ per person)
    - [ ] What's included (checkboxes: flights, accommodation, food, activities)
    - [ ] Flexibility level (radio: "hard limit" / "prefer under" / "no limit")
  - **Destination Preferences**
    - [ ] Vibes multi-select: Beach, City, Nature, Adventure, Relaxation, Nightlife, Culture, Food-focused, Road trip
    - [ ] Specific places in mind (optional text)
    - [ ] Places to avoid (optional text)
    - [ ] Domestic vs International (radio: domestic / international / either)
  - **Constraints & Dealbreakers**
    - [ ] Dietary restrictions (multi-select: vegetarian, vegan, gluten-free, halal, kosher, allergies + other text)
    - [ ] Accessibility needs (multi-select + other text)
    - [ ] Hard no's (text field: "no camping", "no red-eyes", etc.)
  - **Additional Notes**
    - [ ] Open text field
- [ ] Member can edit preferences until trip is locked
- [ ] Form validates required fields before submission

#### Trip Dashboard
- [ ] Shows trip name, status, and invite link
- [ ] List of members with response status (responded / pending)
- [ ] Aggregated preference summary:
  - [ ] Date range overlap visualization (show common available window)
  - [ ] Budget range overlap (min/max across group)
  - [ ] Common vibes (intersection)
  - [ ] Flagged conflicts (no date overlap, budget mismatch, etc.)
- [ ] Organizer can proceed to recommendations when ready (even if not all responded)

#### AI Destination Recommendations
- [ ] "Generate Recommendations" button (organizer only, or configurable)
- [ ] AI receives aggregated preferences and returns 3-5 destination options
- [ ] Each recommendation includes:
  - [ ] Destination name and region
  - [ ] Why it fits the group (AI reasoning)
  - [ ] Estimated cost per person (range)
  - [ ] Sample 2-day highlight itinerary
  - [ ] Tradeoffs or notes (e.g., "slightly over Alex's ideal budget")
- [ ] Members can upvote/downvote each option
- [ ] Organizer selects final destination (or uses vote winner)

#### AI Itinerary Generation
- [ ] Once destination selected, "Generate Itinerary" button
- [ ] AI generates full day-by-day itinerary based on:
  - [ ] Trip length
  - [ ] Group budget
  - [ ] Group vibes/preferences
  - [ ] Constraints (dietary, accessibility)
- [ ] Itinerary structure per day:
  - [ ] Morning / Afternoon / Evening blocks
  - [ ] Activity name and description
  - [ ] Estimated cost
  - [ ] Location (text, optionally linkable)
  - [ ] Duration estimate
  - [ ] Tips/notes
- [ ] Total estimated trip cost displayed

#### Itinerary View
- [ ] Clean, readable day-by-day view
- [ ] Collapsible days
- [ ] Mobile-friendly layout
- [ ] Organizer can "Finalize" itinerary (locks editing)

### P1 - Should Have

- [ ] Nudge button: sends email reminder to members who haven't submitted preferences
- [ ] Regenerate itinerary with modification prompt (text input for tweaks)
- [ ] Member can flag itinerary items (thumbs down + optional reason)
- [ ] Member can suggest additions (form: day, time slot, activity idea)
- [ ] Export itinerary to PDF
- [ ] Export itinerary to Google Calendar (.ics or direct integration)
- [ ] Trip status progression: `collecting` → `recommending` → `planning` → `finalized`
- [ ] Status badge visible on dashboard

### P2 - Nice to Have

- [ ] Packing list generator (AI-based on destination + activities)
- [ ] Cost splitting view (who owes what, if costs are logged)
- [ ] Google Places API integration for richer activity details
- [ ] Multiple itinerary versions (A/B compare)
- [ ] Archive past trips
- [ ] Trip cover photo / customization
- [ ] Activity booking links (affiliate or direct)

---

## Acceptance Criteria

### Trip Creation
- [ ] User can create trip and receive unique invite link
- [ ] Invite link works for unauthenticated users (redirects to sign-in, then joins trip)
- [ ] Creator is automatically added as organizer

### Preference Collection
- [ ] All form fields save correctly to database
- [ ] User can return and edit preferences before lock
- [ ] Form handles edge cases (all "flexible" selections, empty optional fields)

### Aggregation
- [ ] Dashboard correctly computes date overlap (or shows "no overlap" warning)
- [ ] Budget range shows group min/max
- [ ] Vibes show intersection and union

### AI Recommendations
- [ ] AI returns valid JSON with 3-5 options
- [ ] Each option has required fields (name, reasoning, cost, sample itinerary)
- [ ] Handles edge case: impossible constraints (surfaces conflict, suggests compromise)
- [ ] Voting tallies correctly

### AI Itinerary
- [ ] Itinerary covers all trip days
- [ ] Each day has morning/afternoon/evening activities
- [ ] Total cost estimate is sum of activity costs
- [ ] Itinerary respects stated constraints (dietary, accessibility)

### Finalization
- [ ] Finalized itinerary is read-only for all members
- [ ] Export produces valid PDF / .ics file

---

## Technical Notes

### Stack
- **Frontend & Backend**: SvelteKit (CMSaasStarter template)
- **Backend**: FastAPI (Python)
- **Database & Auth**: Supabase (Postgres + Auth + Row Level Security)
- **AI**: Google AI (Gemini via ADK or direct API)
- **OAuth**: Google OAuth (via Supabase Auth)

### Template Baseline (CMSaasStarter)
Using: authentication, user dashboard, profile settings, marketing page, blog, email sending
Not using: Stripe billing, pricing page, subscription management

### API Design Approach
- SvelteKit frontend calls FastAPI backend
- FastAPI handles business logic and AI calls
- Supabase client used directly for auth; backend uses service role for DB writes
- Use SvelteKit load functions for data fetching (no real-time, just refresh/invalidate)

### AI Integration
- Use Gemini API for:
  - Destination recommendation generation
  - Full itinerary generation
  - (P2) Packing list generation
- Prompt engineering required for consistent structured output (JSON mode)
- Consider retry logic for malformed AI responses

### Key Patterns
- Invite codes: short alphanumeric (e.g., `abc123`), stored in `trips.invite_code`
- Trip status: enum column, state machine enforced in backend
- Preferences: JSONB column for flexibility, validated at API layer
- Itinerary: JSONB column with structured day/activity schema

### File Structure (suggested)
```
/src/routes/
  /trips/
    +page.svelte              # List user's trips
    /new/+page.svelte         # Create trip
    /[tripId]/
      +page.svelte            # Trip dashboard
      /preferences/+page.svelte
      /recommendations/+page.svelte
      /itinerary/+page.svelte
  /join/[inviteCode]/+page.svelte  # Join flow

/api/ (FastAPI)
  /trips/
  /preferences/
  /recommendations/
  /itinerary/
```

---

## Out of Scope

- Real-time collaboration / live updates (use refresh/invalidate pattern instead)
- Chat or messaging between members (form-based only)
- Payment processing / Stripe integration
- Actual booking transactions (links only, no purchases)
- Multi-currency support (USD only for MVP)
- Native mobile apps (responsive web only)
- Admin panel for managing all users/trips
- Analytics dashboard
- Social features (public trips, trip sharing, social login beyond Google)
- Offline support
- Internationalization (English only)

---

## Open Questions (Decisions Needed Before Dev)

1. **Trip status transitions**: Can organizer move backward (e.g., re-open preferences after recommendations)?
2. **Late joiners**: If someone joins after recommendations are generated, do they still fill out preferences? Does it trigger re-generation?
3. **AI context enrichment**: Should we pass additional context to AI (e.g., "group of college students", "traveling from Georgia")? If so, where is this collected?
4. **Itinerary edit flow**: Can organizer manually edit itinerary items, or only regenerate via AI?
5. **Vote threshold**: Auto-select destination at X votes, or always manual organizer selection?
6. **Preference visibility**: Can members see each other's individual preferences, or only aggregated view?

---

## Milestones (Suggested)

### Milestone 1: Foundation
- [ ] Fork CMSaasStarter, remove Stripe
- [ ] Set up FastAPI backend with Supabase connection
- [ ] Trip CRUD (create, read, list)
- [ ] Invite link generation and join flow

### Milestone 2: Preferences
- [ ] Preference form UI
- [ ] Preference storage and retrieval
- [ ] Dashboard member list with status

### Milestone 3: Aggregation & Recommendations
- [ ] Preference aggregation logic
- [ ] Dashboard aggregation display
- [ ] AI recommendation integration
- [ ] Voting UI

### Milestone 4: Itinerary
- [ ] AI itinerary generation
- [ ] Itinerary display UI
- [ ] Finalization flow

### Milestone 5: Polish
- [ ] Export (PDF, calendar)
- [ ] Nudge emails
- [ ] Edge case handling
- [ ] Mobile responsiveness pass

---

## Appendix: Sample AI Prompts

### Destination Recommendation Prompt (Rough)
```
You are a travel planning assistant. Given the following group preferences, suggest 3-5 destination options.

Group size: {member_count}
Date window: {earliest_start} to {latest_end}
Trip length: {ideal_length}
Budget range: ${min_budget} - ${max_budget} per person (includes: {inclusions})
Preferred vibes: {vibes_list}
Constraints: {constraints}
Places to avoid: {avoid_list}
Additional notes: {notes}

For each destination, provide:
- name: destination name
- region: country/region
- reasoning: why this fits the group (2-3 sentences)
- estimated_cost_per_person: {min: X, max: Y}
- sample_itinerary: [{day: 1, highlights: ["...", "..."]}, ...]
- tradeoffs: any concerns or compromises (optional)

Respond in JSON format.
```

### Itinerary Generation Prompt (Rough)
```
You are a travel planning assistant. Generate a detailed day-by-day itinerary.

Destination: {destination}
Dates: {start_date} to {end_date}
Group size: {member_count}
Budget: ${budget} per person
Vibes: {vibes}
Dietary restrictions: {dietary}
Accessibility needs: {accessibility}
Things to avoid: {avoid}

For each day, provide morning, afternoon, and evening activities:
- time_block: "morning" | "afternoon" | "evening"
- activity: name of activity
- description: 1-2 sentences
- estimated_cost: number (per person)
- duration: e.g., "2 hours"
- location: address or area name
- tips: optional helpful notes

Respond in JSON format with structure: {days: [{date, activities: [...]}]}
```
