# API Models Documentation

This directory contains all Pydantic models for request/response validation in the TripSync API.

## Model Categories

### 1. Preferences Models (`preferences.py`)

Models for handling user preferences and aggregation:

- **DatePreferences**: Individual user's date availability
- **BudgetPreferences**: Individual user's budget constraints
- **DestinationPreferences**: Individual user's destination preferences (vibes, locations)
- **ConstraintsPreferences**: Individual user's constraints (dietary, accessibility, deal-breakers)
- **AggregatedPreferences**: Computed aggregation of all group members' preferences
- **Conflict**: Represents detected conflicts between member preferences

### 2. Recommendations Models (`recommendations.py`)

Models for destination recommendation generation:

- **SampleHighlight**: A single activity/highlight for a destination (used in 2-day sample)
- **DestinationRecommendation**: A complete destination recommendation with reasoning, cost, highlights, and tradeoffs
- **GenerateRecommendationsRequest**: Request to generate recommendations for a trip
- **GenerateRecommendationsResponse**: Response containing 3-5 destination recommendations

### 3. Itinerary Models (`itinerary.py`)

Models for full itinerary generation:

- **Activity**: A single activity in the itinerary (morning/afternoon/evening)
- **DayItinerary**: Complete itinerary for one day with all activities
- **GenerateItineraryRequest**: Request to generate full trip itinerary
- **GenerateItineraryResponse**: Response containing day-by-day itinerary with total costs
- **RegenerateItineraryRequest**: Request to regenerate itinerary with user feedback

## Validation Rules

### Budget and Cost Validation
- All budget and cost fields must be non-negative (`ge=0`)
- Budget min/max and cost estimates validated as floats

### Date Validation
- Uses Python's `date` type for type safety
- Ensures proper date formats

### Length Validation
- Recommendations: Must return 3-5 destinations (min_length=3, max_length=5)
- Activities: Each day must have at least 1 activity (min_length=1)
- Sample highlights: Must have at least 1 highlight (min_length=1)
- Feedback: Must be 1-1000 characters (min_length=1, max_length=1000)

### Duration Validation
- Activity duration must be > 0 hours (`gt=0`)

### Optional Fields
- Many fields are `Optional[str]` or `Optional[List]` to support flexible user input
- Empty lists default to `[]` using `default_factory=list`

## Usage Examples

### Creating Aggregated Preferences
```python
from api.models import AggregatedPreferences, Conflict

conflict = Conflict(
    type="date_overlap",
    description="No common dates between Alice and Bob",
    affected_members=["alice_id", "bob_id"]
)

agg_prefs = AggregatedPreferences(
    common_start_earliest=date(2026, 5, 1),
    common_end_latest=date(2026, 5, 10),
    date_overlap_days=9,
    budget_min=500.0,
    budget_max=2000.0,
    budget_average=1250.0,
    common_vibes=["Beach", "Relaxation"],
    all_vibes=["Beach", "Relaxation", "City"],
    domestic_international_preference="either",
    all_dietary_restrictions=["vegetarian"],
    all_accessibility_needs=["wheelchair accessible"],
    all_hard_nos=["No camping"],
    conflicts=[conflict],
    total_members=5,
    responded_members=4,
    response_rate=80.0
)
```

### Creating a Destination Recommendation
```python
from api.models import DestinationRecommendation, SampleHighlight

recommendation = DestinationRecommendation(
    name="Tulum",
    region="Mexico",
    reasoning="Perfect mix of beach relaxation and cultural exploration",
    cost_estimate_min=800.0,
    cost_estimate_max=1200.0,
    sample_highlights=[
        SampleHighlight(
            day=1,
            title="Beach Day",
            description="Relax at the stunning Caribbean beaches"
        ),
        SampleHighlight(
            day=2,
            title="Mayan Ruins Tour",
            description="Explore ancient Mayan archaeological sites"
        )
    ],
    tradeoffs="Requires international travel; slightly higher cost"
)
```

### Creating an Itinerary
```python
from api.models import Activity, DayItinerary, GenerateItineraryResponse
from uuid import uuid4

activities = [
    Activity(
        name="Breakfast at Local Cafe",
        description="Enjoy authentic Mexican breakfast",
        time_slot="morning",
        estimated_cost=15.0,
        location="Cafe Luna, Tulum",
        location_url="https://maps.google.com/...",
        duration_hours=1.5,
        tips="Try the chilaquiles!",
        category="dining"
    ),
    Activity(
        name="Beach Time",
        description="Relax at Playa Paraiso",
        time_slot="afternoon",
        estimated_cost=0.0,
        location="Playa Paraiso",
        duration_hours=4.0,
        tips="Bring sunscreen and water",
        category="activity"
    )
]

day = DayItinerary(
    day_number=1,
    date="2026-05-01",
    title="Arrival & Beach Day",
    activities=activities,
    total_cost=15.0
)

itinerary = GenerateItineraryResponse(
    trip_id=uuid4(),
    destination_name="Tulum",
    days=[day],
    total_cost=15.0,
    trip_length_days=1,
    generated_at="2026-01-29T12:00:00Z",
    summary="Relaxing beach getaway with cultural experiences"
)
```

## Testing

All models have comprehensive unit tests in `agent/test_models.py`. Run tests with:

```bash
uv run pytest test_models.py -v
```

Current test coverage:
- ✅ Valid model creation
- ✅ Validation rule enforcement (negative costs, empty strings, etc.)
- ✅ Min/max length constraints
- ✅ Optional vs required fields
- ✅ Nested model validation

## Integration with FastAPI

These models are designed to work seamlessly with FastAPI's automatic request/response validation:

```python
from fastapi import FastAPI, Depends
from api.models import GenerateItineraryRequest, GenerateItineraryResponse
from api.middleware import get_current_user, TokenData

app = FastAPI()

@app.post("/api/trips/{trip_id}/itinerary", response_model=GenerateItineraryResponse)
async def generate_itinerary(
    trip_id: UUID,
    request: GenerateItineraryRequest,
    current_user: TokenData = Depends(get_current_user)
):
    # FastAPI automatically validates request body against GenerateItineraryRequest
    # and serializes response according to GenerateItineraryResponse
    ...
```

## Future Enhancements

Consider adding:
- [ ] More granular date validation (end date after start date)
- [ ] Budget range validation (min <= max)
- [ ] Enum types for fixed values (vibes, flexibility levels, time slots)
- [ ] Custom validators for complex business logic
- [ ] Response examples in docstrings for OpenAPI documentation
