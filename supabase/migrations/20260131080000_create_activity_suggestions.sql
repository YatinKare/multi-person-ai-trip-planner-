-- Create activity_suggestions table for member activity suggestions
CREATE TABLE activity_suggestions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  trip_id uuid NOT NULL REFERENCES trips(id) ON DELETE CASCADE,
  user_id uuid NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  day_index integer NOT NULL,
  time_slot text NOT NULL CHECK (time_slot IN ('morning', 'afternoon', 'evening')),
  activity_name text NOT NULL,
  activity_description text,
  estimated_cost numeric,
  location text,
  reason text,
  status text NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'accepted', 'rejected')),
  reviewed_by uuid REFERENCES profiles(id) ON DELETE SET NULL,
  reviewed_at timestamptz,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- Create indexes for efficient querying
CREATE INDEX idx_activity_suggestions_trip_id ON activity_suggestions(trip_id);
CREATE INDEX idx_activity_suggestions_user_id ON activity_suggestions(user_id);
CREATE INDEX idx_activity_suggestions_status ON activity_suggestions(status);

-- Enable Row Level Security
ALTER TABLE activity_suggestions ENABLE ROW LEVEL SECURITY;

-- RLS Policies for activity_suggestions

-- Members of a trip can view all suggestions for that trip
CREATE POLICY "Members can view trip suggestions"
  ON activity_suggestions
  FOR SELECT
  USING (
    trip_id IN (
      SELECT trip_id FROM trip_members WHERE user_id = auth.uid()
    )
  );

-- Members can insert their own suggestions
CREATE POLICY "Members can create suggestions"
  ON activity_suggestions
  FOR INSERT
  WITH CHECK (
    user_id = auth.uid() AND
    trip_id IN (
      SELECT trip_id FROM trip_members WHERE user_id = auth.uid()
    )
  );

-- Users can update their own pending suggestions
CREATE POLICY "Users can update own pending suggestions"
  ON activity_suggestions
  FOR UPDATE
  USING (user_id = auth.uid() AND status = 'pending')
  WITH CHECK (user_id = auth.uid() AND status = 'pending');

-- Users can delete their own pending suggestions
CREATE POLICY "Users can delete own pending suggestions"
  ON activity_suggestions
  FOR DELETE
  USING (user_id = auth.uid() AND status = 'pending');

-- Organizers can update suggestions (for review/acceptance)
CREATE POLICY "Organizers can review suggestions"
  ON activity_suggestions
  FOR UPDATE
  USING (
    trip_id IN (
      SELECT trip_id FROM trip_members
      WHERE user_id = auth.uid() AND role = 'organizer'
    )
  );

-- Update trigger for updated_at
CREATE TRIGGER update_activity_suggestions_updated_at
  BEFORE UPDATE ON activity_suggestions
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();
