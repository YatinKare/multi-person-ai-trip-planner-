# TripSync FastAPI Backend

This is the FastAPI backend for TripSync that handles AI-powered destination recommendations and itinerary generation using Google ADK (Agent Development Kit).

## Features

- **JWT Authentication**: Validates Supabase JWT tokens for secure API access
- **AI Recommendations**: Generates destination recommendations based on group preferences
- **AI Itinerary Generation**: Creates full day-by-day trip itineraries
- **Preference Aggregation**: Computes group consensus from individual preferences
- **Database Integration**: Connects to Supabase PostgreSQL with Row Level Security

## Prerequisites

- Python 3.13+ (managed via uv)
- Supabase account with database and authentication configured
- Google Gemini API key for AI features

## Setup

1. **Install dependencies**:
   ```bash
   uv sync
   ```

2. **Configure environment variables**:
   Create a `.env.local` file in the project root with:
   ```env
   # Supabase settings
   PUBLIC_SUPABASE_URL=https://your-project.supabase.co
   PRIVATE_SUPABASE_SERVICE_ROLE=your-service-role-key
   SUPABASE_JWT_SECRET=your-jwt-secret

   # Gemini API
   GEMINI_API_KEY=your-gemini-api-key

   # FastAPI settings (optional)
   FASTAPI_PORT=8000
   FASTAPI_HOST=0.0.0.0
   FASTAPI_RELOAD=true
   FASTAPI_LOG_LEVEL=info
   ALLOWED_ORIGINS=http://localhost:5173,https://yourdomain.com
   ```

## Development

### Start the development server

The easiest way to start the server with hot reload:

```bash
uv run python dev.py
```

This will:
- Start FastAPI on port 8000 (or `FASTAPI_PORT` if set)
- Enable hot reload on file changes
- Configure detailed logging
- Validate required environment variables

Alternative method using uvicorn directly:

```bash
uv run uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### Access the API

Once running, you can access:

- **API Root**: http://localhost:8000/
- **Health Check**: http://localhost:8000/health
- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Testing

Run the test suite:

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest test_jwt_middleware.py -v

# Run with coverage
uv run pytest --cov=api --cov-report=html
```

## Project Structure

```
agent/
├── api/                      # FastAPI application
│   ├── main.py              # App entry point with CORS and routes
│   ├── database.py          # Supabase client and database utilities
│   ├── middleware/          # Authentication middleware
│   │   └── auth.py          # JWT token validation
│   ├── routers/             # API route handlers (to be added)
│   ├── models/              # Pydantic models for validation
│   │   ├── preferences.py   # Preference and aggregation models
│   │   ├── recommendations.py # Destination recommendation models
│   │   └── itinerary.py     # Itinerary generation models
│   └── services/            # Business logic (to be added)
├── tripsync/                # Google ADK agents (to be implemented)
│   └── agent.py            # Agent definitions
├── dev.py                   # Development server startup script
└── pyproject.toml          # Python dependencies and project config
```

## API Endpoints

### Authentication

All protected endpoints require a valid Supabase JWT token in the Authorization header:

```
Authorization: Bearer <your-jwt-token>
```

### Available Endpoints

- `GET /` - Health check
- `GET /health` - Detailed health status (API, database, AI)
- `GET /api/me` - Get current user info (protected)

### Upcoming Endpoints

- `POST /api/trips/{trip_id}/recommendations` - Generate destination recommendations
- `POST /api/trips/{trip_id}/itinerary` - Generate trip itinerary
- `POST /api/trips/{trip_id}/itinerary/regenerate` - Regenerate itinerary with feedback

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `PUBLIC_SUPABASE_URL` | Yes | - | Supabase project URL |
| `PRIVATE_SUPABASE_SERVICE_ROLE` | Yes | - | Supabase service role key (bypasses RLS) |
| `SUPABASE_JWT_SECRET` | Yes | - | JWT secret for token validation |
| `GEMINI_API_KEY` | Yes | - | Google Gemini API key for AI |
| `FASTAPI_PORT` | No | 8000 | Port for FastAPI server |
| `FASTAPI_HOST` | No | 0.0.0.0 | Host for FastAPI server |
| `FASTAPI_RELOAD` | No | true | Enable hot reload in development |
| `FASTAPI_LOG_LEVEL` | No | info | Logging level (debug, info, warning, error) |
| `ALLOWED_ORIGINS` | No | http://localhost:5173 | CORS allowed origins (comma-separated) |

## Architecture

### Authentication Flow

1. SvelteKit frontend authenticates user with Supabase Auth (Google OAuth)
2. Frontend receives JWT token from Supabase
3. Frontend sends JWT in Authorization header to FastAPI
4. FastAPI validates JWT using `SUPABASE_JWT_SECRET`
5. FastAPI extracts user_id from token and processes request

### Database Access

- **Frontend**: Uses Supabase client with user's JWT (RLS enforced)
- **Backend**: Uses service role key (bypasses RLS, must check permissions in code)
- **RLS Policies**: Defined in database migrations, ensure users can only access their trips

### AI Integration

- Google ADK runs via `uv run adk ...` commands
- Agent definitions in `tripsync/agent.py`
- FastAPI endpoints orchestrate agent execution
- Results stored in Supabase database

## Troubleshooting

### "No module named 'api'"

Make sure you're running commands from the `agent/` directory:

```bash
cd agent
uv run python dev.py
```

### "Missing required environment variables"

Ensure `.env.local` exists in the project root (one level up from `agent/`) and contains all required variables.

### Database connection failed

1. Check that `PUBLIC_SUPABASE_URL` and `PRIVATE_SUPABASE_SERVICE_ROLE` are correct
2. Verify your Supabase project is running
3. Check network connectivity

### JWT validation fails

1. Ensure `SUPABASE_JWT_SECRET` matches your Supabase project's JWT secret
2. Check that the JWT token is valid and not expired
3. Verify the token includes a `sub` (subject) claim with the user ID

## Contributing

When adding new features:

1. Add Pydantic models to `api/models/`
2. Create router files in `api/routers/`
3. Implement business logic in `api/services/`
4. Add tests in `test_*.py` files
5. Update this README with new endpoints and environment variables

## License

See project root LICENSE file.
