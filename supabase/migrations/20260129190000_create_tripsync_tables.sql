-- Create enum types
CREATE TYPE trip_status AS ENUM ('collecting', 'recommending', 'voting', 'planning', 'finalized');
CREATE TYPE member_role AS ENUM ('organizer', 'member');
CREATE TYPE vote_type AS ENUM ('upvote', 'downvote');

-- Create trips table
CREATE TABLE trips (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    created_by UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    invite_code TEXT NOT NULL UNIQUE,
    status trip_status NOT NULL DEFAULT 'collecting',
    rough_timeframe TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create trip_members junction table
CREATE TABLE trip_members (
    trip_id UUID NOT NULL REFERENCES trips(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    role member_role NOT NULL DEFAULT 'member',
    joined_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    nudged_at TIMESTAMPTZ,
    PRIMARY KEY (trip_id, user_id)
);

-- Create preferences table
CREATE TABLE preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trip_id UUID NOT NULL REFERENCES trips(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    dates JSONB NOT NULL DEFAULT '{}',
    budget JSONB NOT NULL DEFAULT '{}',
    destination_prefs JSONB NOT NULL DEFAULT '{}',
    constraints JSONB NOT NULL DEFAULT '{}',
    notes TEXT,
    submitted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(trip_id, user_id)
);

-- Create recommendations table
CREATE TABLE recommendations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trip_id UUID NOT NULL REFERENCES trips(id) ON DELETE CASCADE,
    destinations JSONB NOT NULL DEFAULT '[]',
    generated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    generated_by UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE
);

-- Create destination_votes table
CREATE TABLE destination_votes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    recommendation_id UUID NOT NULL REFERENCES recommendations(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    destination_index INTEGER NOT NULL,
    vote_type vote_type NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(recommendation_id, user_id, destination_index)
);

-- Create itineraries table
CREATE TABLE itineraries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trip_id UUID NOT NULL REFERENCES trips(id) ON DELETE CASCADE,
    destination_name TEXT NOT NULL,
    days JSONB NOT NULL DEFAULT '[]',
    total_cost NUMERIC(10, 2),
    generated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    finalized_at TIMESTAMPTZ,
    finalized_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    UNIQUE(trip_id)
);

-- Create function to generate unique invite codes
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

        -- Check if code already exists
        SELECT EXISTS(SELECT 1 FROM trips WHERE invite_code = result) INTO code_exists;
    END LOOP;

    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- Create function to check if user is trip organizer
CREATE OR REPLACE FUNCTION is_trip_organizer(trip_uuid UUID, user_uuid UUID)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM trip_members
        WHERE trip_id = trip_uuid
        AND user_id = user_uuid
        AND role = 'organizer'
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create trigger to update trips.updated_at on any change
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_trips_updated_at
    BEFORE UPDATE ON trips
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_preferences_updated_at
    BEFORE UPDATE ON preferences
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Enable Row Level Security on all tables
ALTER TABLE trips ENABLE ROW LEVEL SECURITY;
ALTER TABLE trip_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE recommendations ENABLE ROW LEVEL SECURITY;
ALTER TABLE destination_votes ENABLE ROW LEVEL SECURITY;
ALTER TABLE itineraries ENABLE ROW LEVEL SECURITY;

-- RLS Policies for trips table
-- Users can view trips they're members of
CREATE POLICY "Users can view trips they are members of"
    ON trips FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM trip_members
            WHERE trip_members.trip_id = trips.id
            AND trip_members.user_id = auth.uid()
        )
    );

-- Users can insert trips (they'll become organizer via trigger)
CREATE POLICY "Users can create trips"
    ON trips FOR INSERT
    WITH CHECK (auth.uid() = created_by);

-- Organizers can update their trips
CREATE POLICY "Organizers can update their trips"
    ON trips FOR UPDATE
    USING (
        EXISTS (
            SELECT 1 FROM trip_members
            WHERE trip_members.trip_id = trips.id
            AND trip_members.user_id = auth.uid()
            AND trip_members.role = 'organizer'
        )
    );

-- Organizers can delete their trips
CREATE POLICY "Organizers can delete their trips"
    ON trips FOR DELETE
    USING (
        EXISTS (
            SELECT 1 FROM trip_members
            WHERE trip_members.trip_id = trips.id
            AND trip_members.user_id = auth.uid()
            AND trip_members.role = 'organizer'
        )
    );

-- RLS Policies for trip_members table
-- Users can view members of trips they're in
CREATE POLICY "Users can view members of trips they are in"
    ON trip_members FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM trip_members tm
            WHERE tm.trip_id = trip_members.trip_id
            AND tm.user_id = auth.uid()
        )
    );

-- Users can insert themselves as members (for joining via invite)
CREATE POLICY "Users can join trips"
    ON trip_members FOR INSERT
    WITH CHECK (auth.uid() = user_id AND role = 'member');

-- Organizers can insert members (for inviting)
CREATE POLICY "Organizers can add members"
    ON trip_members FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM trip_members tm
            WHERE tm.trip_id = trip_members.trip_id
            AND tm.user_id = auth.uid()
            AND tm.role = 'organizer'
        )
    );

-- Users can delete themselves from trips (leave trip)
CREATE POLICY "Users can leave trips"
    ON trip_members FOR DELETE
    USING (auth.uid() = user_id AND role = 'member');

-- Organizers can delete members (kick members)
CREATE POLICY "Organizers can remove members"
    ON trip_members FOR DELETE
    USING (
        EXISTS (
            SELECT 1 FROM trip_members tm
            WHERE tm.trip_id = trip_members.trip_id
            AND tm.user_id = auth.uid()
            AND tm.role = 'organizer'
        )
    );

-- Organizers can update members (for nudging)
CREATE POLICY "Organizers can update members"
    ON trip_members FOR UPDATE
    USING (
        EXISTS (
            SELECT 1 FROM trip_members tm
            WHERE tm.trip_id = trip_members.trip_id
            AND tm.user_id = auth.uid()
            AND tm.role = 'organizer'
        )
    );

-- RLS Policies for preferences table
-- Users can view all preferences for trips they're in
CREATE POLICY "Users can view preferences for trips they are in"
    ON preferences FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM trip_members
            WHERE trip_members.trip_id = preferences.trip_id
            AND trip_members.user_id = auth.uid()
        )
    );

-- Users can insert only their own preferences
CREATE POLICY "Users can create their own preferences"
    ON preferences FOR INSERT
    WITH CHECK (
        auth.uid() = user_id
        AND EXISTS (
            SELECT 1 FROM trip_members
            WHERE trip_members.trip_id = preferences.trip_id
            AND trip_members.user_id = auth.uid()
        )
    );

-- Users can update only their own preferences
CREATE POLICY "Users can update their own preferences"
    ON preferences FOR UPDATE
    USING (auth.uid() = user_id);

-- Users can delete only their own preferences
CREATE POLICY "Users can delete their own preferences"
    ON preferences FOR DELETE
    USING (auth.uid() = user_id);

-- RLS Policies for recommendations table
-- Users can view recommendations for trips they're in
CREATE POLICY "Users can view recommendations for trips they are in"
    ON recommendations FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM trip_members
            WHERE trip_members.trip_id = recommendations.trip_id
            AND trip_members.user_id = auth.uid()
        )
    );

-- Organizers can insert recommendations
CREATE POLICY "Organizers can create recommendations"
    ON recommendations FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM trip_members
            WHERE trip_members.trip_id = recommendations.trip_id
            AND trip_members.user_id = auth.uid()
            AND trip_members.role = 'organizer'
        )
    );

-- RLS Policies for destination_votes table
-- Users can view all votes for trips they're in
CREATE POLICY "Users can view votes for trips they are in"
    ON destination_votes FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM recommendations r
            JOIN trip_members tm ON tm.trip_id = r.trip_id
            WHERE r.id = destination_votes.recommendation_id
            AND tm.user_id = auth.uid()
        )
    );

-- Users can insert only their own votes
CREATE POLICY "Users can create their own votes"
    ON destination_votes FOR INSERT
    WITH CHECK (
        auth.uid() = user_id
        AND EXISTS (
            SELECT 1 FROM recommendations r
            JOIN trip_members tm ON tm.trip_id = r.trip_id
            WHERE r.id = destination_votes.recommendation_id
            AND tm.user_id = auth.uid()
        )
    );

-- Users can update only their own votes
CREATE POLICY "Users can update their own votes"
    ON destination_votes FOR UPDATE
    USING (auth.uid() = user_id);

-- Users can delete only their own votes
CREATE POLICY "Users can delete their own votes"
    ON destination_votes FOR DELETE
    USING (auth.uid() = user_id);

-- RLS Policies for itineraries table
-- Users can view itineraries for trips they're in
CREATE POLICY "Users can view itineraries for trips they are in"
    ON itineraries FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM trip_members
            WHERE trip_members.trip_id = itineraries.trip_id
            AND trip_members.user_id = auth.uid()
        )
    );

-- Organizers can insert itineraries
CREATE POLICY "Organizers can create itineraries"
    ON itineraries FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM trip_members
            WHERE trip_members.trip_id = itineraries.trip_id
            AND trip_members.user_id = auth.uid()
            AND trip_members.role = 'organizer'
        )
    );

-- Organizers can update itineraries
CREATE POLICY "Organizers can update itineraries"
    ON itineraries FOR UPDATE
    USING (
        EXISTS (
            SELECT 1 FROM trip_members
            WHERE trip_members.trip_id = itineraries.trip_id
            AND trip_members.user_id = auth.uid()
            AND trip_members.role = 'organizer'
        )
    );

-- Create indexes for performance
CREATE INDEX idx_trips_invite_code ON trips(invite_code);
CREATE INDEX idx_trips_created_by ON trips(created_by);
CREATE INDEX idx_trip_members_trip_id ON trip_members(trip_id);
CREATE INDEX idx_trip_members_user_id ON trip_members(user_id);
CREATE INDEX idx_preferences_trip_id ON preferences(trip_id);
CREATE INDEX idx_preferences_user_id ON preferences(user_id);
CREATE INDEX idx_recommendations_trip_id ON recommendations(trip_id);
CREATE INDEX idx_destination_votes_recommendation_id ON destination_votes(recommendation_id);
CREATE INDEX idx_destination_votes_user_id ON destination_votes(user_id);
CREATE INDEX idx_itineraries_trip_id ON itineraries(trip_id);

-- Grant permissions
GRANT ALL ON trips TO authenticated;
GRANT ALL ON trip_members TO authenticated;
GRANT ALL ON preferences TO authenticated;
GRANT ALL ON recommendations TO authenticated;
GRANT ALL ON destination_votes TO authenticated;
GRANT ALL ON itineraries TO authenticated;
