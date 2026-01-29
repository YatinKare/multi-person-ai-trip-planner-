# TripSync - AI-Powered Group Trip Planning

## Goal
Build a web application that eliminates group trip planning chaos by collecting structured preferences from all participants and using AI to generate destination recommendations and full itineraries based on the group's aggregated constraints.

## Current State
Group trip planning happens in group chats where people give vague, unstructured responses ("I'm down", "whatever", "budget not really"). No one wants to be the organizer who manually synthesizes constraints. Result: decision paralysis and trips that never happen.

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

## User Flows

### Flow 1: Trip Creation
```
Initiator opens app
→ Signs in with Google OAuth
→ Lands on "My Trips" dashboard (empty state if first time)
→ Clicks "Create Trip"
→ Enters trip name (e.g., "May Trip 2025")
→ Optionally sets rough timeframe hint (e.g., "early May")
→ Clicks "Create"
→ Lands on new trip dashboard
→ Sees shareable invite link prominently displayed
→ Copies link, shares in group chat
```

### Flow 2: Joining a Trip (New User)
```
Friend receives invite link in group chat
→ Clicks link
→ Lands on join page showing trip name and who created it
→ Prompted to sign in with Google
→ After auth, automatically added to trip as member
→ Redirected to preference form for that trip
→ Sees message: "Welcome! Fill out your preferences to help plan the trip."
```

### Flow 3: Joining a Trip (Existing User)
```
Friend receives invite link
→ Clicks link
→ Already signed in (recognized by session)
→ Sees confirmation: "Join [Trip Name]?"
→ Clicks "Join"
→ Added to trip, redirected to preference form
```

### Flow 4: Filling Out Preferences
```
Member lands on preference form
→ Fills out each section:
   1. Dates: selects date range, trip length, flexibility
   2. Budget: adjusts slider, selects inclusions, sets flexibility
   3. Destination: picks vibes, optionally adds specific places/avoids
   4. Constraints: selects dietary/accessibility needs, adds deal-breakers
   5. Notes: adds any additional context
→ Clicks "Submit Preferences"
→ Sees confirmation: "Preferences saved!"
→ Redirected to trip dashboard
→ Can return and edit anytime before trip is locked
```

### Flow 5: Viewing Trip Dashboard (Member)
```
Member navigates to trip from "My Trips"
→ Sees trip overview:
   - Trip name and status
   - List of members with response status (✓ responded / ⏳ pending)
   - "Your preferences" summary (collapsible)
   - Aggregated group data (if enough responses):
     - Date overlap window
     - Budget range
     - Common vibes
   - Any conflicts flagged (e.g., "No date overlap between Alice and Bob")
→ Can click "Edit My Preferences" to update
```

### Flow 6: Viewing Trip Dashboard (Organizer)
```
Organizer navigates to trip
→ Sees everything members see, plus:
   - "Copy Invite Link" button always visible
   - "Nudge" button next to pending members
   - "Generate Recommendations" button (enabled when ready)
   - Trip status controls
→ Can see aggregated view even with partial responses
→ Decides when to proceed (doesn't need 100% response rate)
```

### Flow 7: Nudging Non-Responders
```
Organizer sees pending members on dashboard
→ Clicks "Nudge" next to a member's name
→ System sends email: "Hey [Name], [Organizer] is waiting for your preferences for [Trip Name]!"
→ Button changes to "Nudged" with timestamp
→ Can nudge again after 24 hours
```

### Flow 8: Generating Destination Recommendations
```
Organizer decides group has enough responses
→ Clicks "Generate Recommendations"
→ Loading state: "AI is analyzing your group's preferences..."
→ AI returns 3-5 destination options
→ Each option displayed as a card:
   - Destination name + region
   - Why it fits (AI reasoning)
   - Estimated cost per person
   - 2-day sample highlights
   - Any tradeoffs noted
→ Members can upvote/downvote each option
→ Vote counts visible to all
```

### Flow 9: Voting on Destinations
```
Member views recommendations
→ Sees all destination cards with current vote counts
→ Can upvote (👍) or downvote (👎) each option
→ Can change vote anytime before selection
→ Votes update for all viewers on page refresh
```

### Flow 10: Selecting Final Destination
```
Organizer reviews votes
→ Clicks "Select Destination" on chosen option
→ Confirmation modal: "Select [Destination] as the final destination?"
→ Confirms
→ Trip status changes to "planning"
→ "Generate Itinerary" button appears
```

### Flow 11: Generating Full Itinerary
```
Organizer clicks "Generate Itinerary"
→ Loading state: "AI is building your itinerary..."
→ AI generates day-by-day plan based on:
   - Selected destination
   - Trip dates (from aggregated preferences)
   - Group budget
   - Vibes and constraints
→ Itinerary displayed with:
   - Day-by-day breakdown
   - Morning / Afternoon / Evening activities
   - Estimated costs per activity
   - Locations and tips
   - Total estimated trip cost
```

### Flow 12: Reviewing and Adjusting Itinerary
```
Members view generated itinerary
→ Can flag items they don't like (thumbs down + optional reason)
→ Can suggest additions via form (day, time slot, activity idea)
→ Organizer sees all feedback
→ Organizer can click "Regenerate with Feedback"
→ AI incorporates feedback into new version
→ Repeat until satisfactory
```

### Flow 13: Finalizing Itinerary
```
Organizer satisfied with itinerary
→ Clicks "Finalize Trip"
→ Confirmation: "This will lock the itinerary. Members can still view but not suggest changes."
→ Confirms
→ Trip status changes to "finalized"
→ Itinerary becomes read-only
→ Export options appear (PDF, calendar)
```

### Flow 14: Viewing Finalized Trip
```
Any member opens finalized trip
→ Sees clean itinerary view:
   - Day-by-day schedule
   - All activity details
   - Total cost summary
   - Export buttons
→ Can download PDF
→ Can export to Google Calendar
```

### Flow 15: Exporting Itinerary
```
Member clicks "Export to PDF"
→ PDF generated with formatted itinerary
→ Downloads automatically

Member clicks "Add to Google Calendar"
→ .ics file generated with all activities as events
→ Downloads for import
```

### Flow 16: Managing Multiple Trips
```
User clicks "My Trips" in navigation
→ Sees list of all trips they're part of:
   - Trip name
   - Status badge (collecting / voting / planning / finalized)
   - Member count
   - Last updated date
→ Can filter by status
→ Clicking a trip opens its dashboard
→ Finalized trips show at bottom or in "Past Trips" section
```

### Flow 17: Leaving a Trip
```
Member opens trip they want to leave
→ Clicks "Leave Trip" in settings/menu
→ Confirmation: "Are you sure? Your preferences will be deleted."
→ Confirms
→ Removed from trip, redirected to "My Trips"
→ Organizer cannot leave (must transfer or delete trip)
```

### Flow 18: Deleting a Trip (Organizer Only)
```
Organizer opens trip settings
→ Clicks "Delete Trip"
→ Confirmation: "This will permanently delete the trip and all data. This cannot be undone."
→ Types trip name to confirm
→ Trip deleted, all members removed
→ Redirected to "My Trips"
```

---

## Requirements

### P0 - MVP (Must Ship)

#### Authentication & User Management
- [ ] Google OAuth sign-in only (already configured via Supabase Auth)
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
- [ ] Organizer manually selects final destination

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

#### UI Implementation
- [ ] Convert HTML mockups from `documents/stitch_trip_management_dashboard/` to Svelte components
- [ ] Use DaisyUI Drawer layout pattern from mockups consistently across all screens
- [ ] Apply shared theme from `tripsync-theme.css`
- [ ] New screens not in mockups should follow same DaisyUI patterns and theme

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
- **Frontend**: SvelteKit (CMSaasStarter template, modified)
- **Backend**: FastAPI (Python) - for AI agent orchestration
- **Database & Auth**: Supabase (Postgres + Auth + Row Level Security)
- **AI**: Google ADK (Agent Development Kit) with Gemini
- **OAuth**: Google OAuth only (via Supabase Auth, already configured)
- **Storage**: Supabase Storage (S3-compatible) - env vars `SUPABASE_STORAGE_ACCESS_KEY_ID` and `SUPABASE_STORAGE_SECRET_ACCESS_KEY` available
- **Package Managers**: Bun (frontend), uv (backend Python)

### Template Baseline (CMSaasStarter - Modified)
The following modifications have already been made to the CMSaasStarter template:
- Stripe/billing code removed (not needed for free app)
- Blog engine removed
- Marketing pages removed
- Account pages streamlined
- Google OAuth configured and working

Remaining from template: authentication flow, user dashboard, profile settings, email sending infrastructure

### UI Mockups (Google Stitch)
HTML mockups for key screens are available in `documents/stitch_trip_management_dashboard/`. All mockups:
- Use DaisyUI components with a consistent "Drawer" layout
- Share a common theme via `documents/stitch_trip_management_dashboard/tripsync-theme.css`
- Are ready for straightforward conversion to Svelte components (DaisyUI is already compatible)

These mockups should be used as the design source of truth. Additional screens not covered by mockups should follow the same DaisyUI Drawer pattern and theme.

### API Design Approach
- SvelteKit frontend calls FastAPI backend for all AI-related operations
- FastAPI handles agent orchestration via Google ADK (`uv run adk ...`)
- Protected routes: FastAPI endpoints validate Supabase JWT tokens before processing
- Supabase client used on frontend for auth; backend uses service role key for DB operations
- Use SvelteKit load functions for non-AI data fetching (trips, preferences, etc.)
- AI calls made exclusively through FastAPI to keep ADK logic in Python

### AI Integration (Google ADK)
- Google ADK runs in FastAPI backend (Python)
- All ADK commands run via `uv run adk ...`
- Agent definitions, prompts, tools, and schemas documented separately (link TBD)
- Two primary agent capabilities needed: destination recommendation and itinerary generation

### Key Patterns
- Invite codes: short alphanumeric (e.g., `abc123`), stored in `trips.invite_code`
- Trip status: enum column, state machine enforced in backend
- Preferences: JSONB column for flexibility, validated at API layer
- Itinerary: JSONB column with structured day/activity schema

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

## Milestones (Suggested)

### Milestone 1: Foundation
- [ ] Set up FastAPI backend project with uv
- [ ] Set up Supabase tables (trips, trip_members, preferences)
- [ ] Implement JWT validation middleware in FastAPI (validate Supabase tokens)
- [ ] Convert Stitch HTML mockups to Svelte components (DaisyUI Drawer layout + theme)
- [ ] Trip CRUD in SvelteKit (create, read, list)
- [ ] Invite link generation and join flow

### Milestone 2: Preferences
- [ ] Preference form UI (all fields)
- [ ] Preference storage and retrieval via Supabase
- [ ] Dashboard member list with response status

### Milestone 3: Aggregation & Recommendations
- [ ] Preference aggregation logic
- [ ] Dashboard aggregation display (date overlap, budget range, vibes)
- [ ] Set up Google ADK in FastAPI (`uv run adk ...`)
- [ ] Destination recommendation endpoint
- [ ] Recommendations UI with voting

### Milestone 4: Itinerary
- [ ] Itinerary generation endpoint via ADK
- [ ] Itinerary display UI (day-by-day view)
- [ ] Finalization flow (organizer manually selects, then locks trip)

### Milestone 5: Polish
- [ ] Export (PDF, calendar)
- [ ] Nudge emails (via template email system)
- [ ] Edge case handling (no overlap, impossible constraints)
- [ ] Mobile responsiveness pass
