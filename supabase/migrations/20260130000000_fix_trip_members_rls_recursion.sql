-- Fix infinite recursion in trip_members RLS policy and trip creation flow
-- Issues fixed:
-- 1. SELECT policy on trip_members queries itself, causing infinite recursion
-- 2. No policy allows trip creator to add themselves as organizer (chicken-and-egg)
-- 3. generate_invite_code doesn't bypass RLS, causing potential issues

-- ============================================================================
-- PART 1: Create SECURITY DEFINER helper functions
-- ============================================================================

-- Function to check trip membership (bypasses RLS)
CREATE OR REPLACE FUNCTION is_trip_member(trip_uuid UUID, user_uuid UUID)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM trip_members
        WHERE trip_id = trip_uuid
        AND user_id = user_uuid
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to check if user is the trip creator (bypasses RLS)
CREATE OR REPLACE FUNCTION is_trip_creator(trip_uuid UUID, user_uuid UUID)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM trips
        WHERE id = trip_uuid
        AND created_by = user_uuid
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Fix generate_invite_code to use SECURITY DEFINER
CREATE OR REPLACE FUNCTION generate_invite_code()
RETURNS TEXT AS $$
DECLARE
    chars TEXT := 'abcdefghijklmnopqrstuvwxyz0123456789';
    result TEXT := '';
    i INTEGER;
    code_exists BOOLEAN := TRUE;
BEGIN
    WHILE code_exists LOOP
        result := '';
        FOR i IN 1..8 LOOP
            result := result || substr(chars, floor(random() * length(chars) + 1)::int, 1);
        END LOOP;

        -- Check if code already exists (needs SECURITY DEFINER to see all trips)
        SELECT EXISTS(SELECT 1 FROM trips WHERE invite_code = result) INTO code_exists;
    END LOOP;

    RETURN result;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================================================
-- PART 2: Fix trip_members RLS policies
-- ============================================================================

-- Drop the problematic policies
DROP POLICY IF EXISTS "Users can view members of trips they are in" ON trip_members;
DROP POLICY IF EXISTS "Users can join trips" ON trip_members;
DROP POLICY IF EXISTS "Organizers can add members" ON trip_members;
DROP POLICY IF EXISTS "Organizers can remove members" ON trip_members;
DROP POLICY IF EXISTS "Organizers can update members" ON trip_members;

-- SELECT: Users can view members of trips they're in
CREATE POLICY "Users can view members of trips they are in"
    ON trip_members FOR SELECT
    USING (is_trip_member(trip_id, auth.uid()));

-- INSERT: Users can join trips as member via invite
CREATE POLICY "Users can join trips"
    ON trip_members FOR INSERT
    WITH CHECK (auth.uid() = user_id AND role = 'member');

-- INSERT: Trip creator can add themselves as organizer
CREATE POLICY "Trip creator can add themselves as organizer"
    ON trip_members FOR INSERT
    WITH CHECK (
        auth.uid() = user_id
        AND role = 'organizer'
        AND is_trip_creator(trip_id, auth.uid())
    );

-- INSERT: Existing organizers can add other members
CREATE POLICY "Organizers can add members"
    ON trip_members FOR INSERT
    WITH CHECK (
        is_trip_organizer(trip_id, auth.uid())
        AND auth.uid() != user_id  -- Can't use this policy to add yourself
    );

-- DELETE: Organizers can remove members
CREATE POLICY "Organizers can remove members"
    ON trip_members FOR DELETE
    USING (is_trip_organizer(trip_id, auth.uid()));

-- UPDATE: Organizers can update members
CREATE POLICY "Organizers can update members"
    ON trip_members FOR UPDATE
    USING (is_trip_organizer(trip_id, auth.uid()));
