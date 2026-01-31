-- Create itinerary_feedback table for activity feedback system (Task 8.4)

-- Create feedback table
CREATE TABLE itinerary_feedback (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  itinerary_id uuid NOT NULL REFERENCES itineraries(id) ON DELETE CASCADE,
  user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  day_index integer NOT NULL,
  activity_index integer NOT NULL,
  activity_name text NOT NULL,
  feedback_type text NOT NULL CHECK (feedback_type IN ('dislike')),
  reason text,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now()
);

-- Create index for faster lookups by itinerary
CREATE INDEX idx_itinerary_feedback_itinerary_id ON itinerary_feedback(itinerary_id);

-- Create index for faster lookups by user
CREATE INDEX idx_itinerary_feedback_user_id ON itinerary_feedback(user_id);

-- Create composite unique constraint to prevent duplicate feedback on same activity
CREATE UNIQUE INDEX idx_itinerary_feedback_unique ON itinerary_feedback(itinerary_id, user_id, day_index, activity_index);

-- Enable Row Level Security
ALTER TABLE itinerary_feedback ENABLE ROW LEVEL SECURITY;

-- RLS Policy: Users can view feedback for trips they're members of
CREATE POLICY "Users can view feedback for their trips"
  ON itinerary_feedback
  FOR SELECT
  USING (
    EXISTS (
      SELECT 1
      FROM itineraries i
      JOIN trip_members tm ON tm.trip_id = i.trip_id
      WHERE i.id = itinerary_feedback.itinerary_id
        AND tm.user_id = auth.uid()
    )
  );

-- RLS Policy: Users can insert their own feedback
CREATE POLICY "Users can insert their own feedback"
  ON itinerary_feedback
  FOR INSERT
  WITH CHECK (
    auth.uid() = user_id
    AND EXISTS (
      SELECT 1
      FROM itineraries i
      JOIN trip_members tm ON tm.trip_id = i.trip_id
      WHERE i.id = itinerary_feedback.itinerary_id
        AND tm.user_id = auth.uid()
    )
  );

-- RLS Policy: Users can update their own feedback
CREATE POLICY "Users can update their own feedback"
  ON itinerary_feedback
  FOR UPDATE
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

-- RLS Policy: Users can delete their own feedback
CREATE POLICY "Users can delete their own feedback"
  ON itinerary_feedback
  FOR DELETE
  USING (auth.uid() = user_id);

-- Create trigger to update updated_at timestamp
CREATE TRIGGER update_itinerary_feedback_updated_at
  BEFORE UPDATE ON itinerary_feedback
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();
