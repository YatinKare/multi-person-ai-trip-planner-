-- Add selected_destination_index to recommendations table
ALTER TABLE recommendations
ADD COLUMN selected_destination_index INTEGER,
ADD COLUMN selected_at TIMESTAMPTZ,
ADD COLUMN selected_by UUID REFERENCES auth.users(id) ON DELETE SET NULL;

-- Add comment to explain the column
COMMENT ON COLUMN recommendations.selected_destination_index IS 'Index of the destination that was selected from the destinations JSONB array';
