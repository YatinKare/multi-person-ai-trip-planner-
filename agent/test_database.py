"""
Test suite for database connection and utility functions.

Run with: uv run pytest test_database.py -v
"""
import pytest
from api.database import (
    get_supabase_client,
    check_database_connection,
    get_trip_by_id,
    is_user_trip_member,
    is_user_trip_organizer,
)


def test_get_supabase_client():
    """Test that we can get a Supabase client instance."""
    client = get_supabase_client()
    assert client is not None, "Supabase client should not be None"


@pytest.mark.asyncio
async def test_database_connection():
    """Test that database connection is healthy."""
    is_healthy = await check_database_connection()
    assert is_healthy is True, "Database connection should be healthy"


@pytest.mark.asyncio
async def test_get_trip_by_id_nonexistent():
    """Test fetching a trip that doesn't exist returns None."""
    # Use a UUID that definitely doesn't exist
    fake_uuid = "00000000-0000-0000-0000-000000000000"
    trip = await get_trip_by_id(fake_uuid)
    assert trip is None, "Non-existent trip should return None"


@pytest.mark.asyncio
async def test_is_user_trip_member_nonexistent():
    """Test checking membership for non-existent trip/user returns False."""
    fake_user_uuid = "00000000-0000-0000-0000-000000000001"
    fake_trip_uuid = "00000000-0000-0000-0000-000000000002"
    is_member = await is_user_trip_member(fake_user_uuid, fake_trip_uuid)
    assert is_member is False, "Non-existent membership should return False"


@pytest.mark.asyncio
async def test_is_user_trip_organizer_nonexistent():
    """Test checking organizer status for non-existent trip/user returns False."""
    fake_user_uuid = "00000000-0000-0000-0000-000000000001"
    fake_trip_uuid = "00000000-0000-0000-0000-000000000002"
    is_organizer = await is_user_trip_organizer(fake_user_uuid, fake_trip_uuid)
    assert is_organizer is False, "Non-existent organizer should return False"


if __name__ == "__main__":
    # Run tests with: uv run python test_database.py
    pytest.main([__file__, "-v"])
