-- Allow authenticated users to view trips by invite code
-- This is needed for the join flow where a user receives an invite link
-- but isn't yet a member of the trip

-- Also allow viewing profiles of any user (needed to show organizer info on join page)
DROP POLICY IF EXISTS "Profiles are viewable by self." ON profiles;

CREATE POLICY "Profiles are viewable by authenticated users"
    ON profiles FOR SELECT
    USING (auth.uid() IS NOT NULL);

-- Add policy to allow viewing trips by invite code
CREATE POLICY "Users can view trips by invite code"
    ON trips FOR SELECT
    USING (
        auth.uid() IS NOT NULL
        AND invite_code IS NOT NULL
    );
