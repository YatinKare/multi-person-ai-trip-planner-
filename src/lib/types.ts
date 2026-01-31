// Type for activity in an itinerary
export interface Activity {
  name: string;
  description: string;
  time_slot: string;
  estimated_cost: number;
  location: string;
  location_url?: string;
  duration_hours: number;
  tips?: string;
  category?: string;
}

// Type for a day in an itinerary
export interface DayItinerary {
  day_number: number;
  date?: string;
  title?: string;
  activities: Activity[];
  total_cost: number;
}
