-- Add regeneration_count column to itineraries table
-- This tracks how many times an itinerary has been regenerated with feedback

ALTER TABLE itineraries
ADD COLUMN IF NOT EXISTS regeneration_count INTEGER NOT NULL DEFAULT 0;

-- Add check constraint to ensure regeneration_count is non-negative and not too high
ALTER TABLE itineraries
ADD CONSTRAINT itineraries_regeneration_count_check CHECK (regeneration_count >= 0 AND regeneration_count <= 10);

-- Update existing itineraries to have regeneration_count = 0
UPDATE itineraries
SET regeneration_count = 0
WHERE regeneration_count IS NULL;
