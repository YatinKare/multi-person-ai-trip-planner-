export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[]

export interface Database {
  public: {
    Tables: {
      contact_requests: {
        Row: {
          company_name: string | null
          email: string | null
          first_name: string | null
          id: string
          last_name: string | null
          message_body: string | null
          phone: string | null
          updated_at: Date | null
        }
        Insert: {
          company_name?: string | null
          email?: string | null
          first_name?: string | null
          id?: string
          last_name?: string | null
          message_body?: string | null
          phone?: string | null
          updated_at?: Date | null
        }
        Update: {
          company_name?: string | null
          email?: string | null
          first_name?: string | null
          id?: string
          last_name?: string | null
          message_body?: string | null
          phone?: string | null
          updated_at?: Date | null
        }
        Relationships: []
      }
      profiles: {
        Row: {
          avatar_url: string | null
          full_name: string | null
          id: string
          updated_at: string | null
          company_name: string | null
          website: string | null
          unsubscribed: boolean
        }
        Insert: {
          avatar_url?: string | null
          full_name?: string | null
          id: string
          updated_at?: Date | null
          company_name?: string | null
          website?: string | null
          unsubscribed: boolean
        }
        Update: {
          avatar_url?: string | null
          full_name?: string | null
          id?: string
          updated_at?: string | null
          company_name?: string | null
          website?: string | null
          unsubscribed: boolean
        }
        Relationships: [
          {
            foreignKeyName: "profiles_id_fkey"
            columns: ["id"]
            referencedRelation: "users"
            referencedColumns: ["id"]
          },
        ]
      }
      trips: {
        Row: {
          id: string
          name: string
          created_by: string
          invite_code: string
          status: Database["public"]["Enums"]["trip_status"]
          rough_timeframe: string | null
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          name: string
          created_by: string
          invite_code: string
          status?: Database["public"]["Enums"]["trip_status"]
          rough_timeframe?: string | null
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          name?: string
          created_by?: string
          invite_code?: string
          status?: Database["public"]["Enums"]["trip_status"]
          rough_timeframe?: string | null
          created_at?: string
          updated_at?: string
        }
        Relationships: [
          {
            foreignKeyName: "trips_created_by_fkey"
            columns: ["created_by"]
            referencedRelation: "users"
            referencedColumns: ["id"]
          },
        ]
      }
      trip_members: {
        Row: {
          trip_id: string
          user_id: string
          role: Database["public"]["Enums"]["member_role"]
          joined_at: string
          nudged_at: string | null
        }
        Insert: {
          trip_id: string
          user_id: string
          role?: Database["public"]["Enums"]["member_role"]
          joined_at?: string
          nudged_at?: string | null
        }
        Update: {
          trip_id?: string
          user_id?: string
          role?: Database["public"]["Enums"]["member_role"]
          joined_at?: string
          nudged_at?: string | null
        }
        Relationships: [
          {
            foreignKeyName: "trip_members_trip_id_fkey"
            columns: ["trip_id"]
            referencedRelation: "trips"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "trip_members_user_id_fkey"
            columns: ["user_id"]
            referencedRelation: "users"
            referencedColumns: ["id"]
          },
        ]
      }
      preferences: {
        Row: {
          id: string
          trip_id: string
          user_id: string
          dates: Json
          budget: Json
          destination_prefs: Json
          constraints: Json
          notes: string | null
          submitted_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          trip_id: string
          user_id: string
          dates?: Json
          budget?: Json
          destination_prefs?: Json
          constraints?: Json
          notes?: string | null
          submitted_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          trip_id?: string
          user_id?: string
          dates?: Json
          budget?: Json
          destination_prefs?: Json
          constraints?: Json
          notes?: string | null
          submitted_at?: string
          updated_at?: string
        }
        Relationships: [
          {
            foreignKeyName: "preferences_trip_id_fkey"
            columns: ["trip_id"]
            referencedRelation: "trips"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "preferences_user_id_fkey"
            columns: ["user_id"]
            referencedRelation: "users"
            referencedColumns: ["id"]
          },
        ]
      }
      recommendations: {
        Row: {
          id: string
          trip_id: string
          destinations: Json
          generated_at: string
          generated_by: string
        }
        Insert: {
          id?: string
          trip_id: string
          destinations?: Json
          generated_at?: string
          generated_by: string
        }
        Update: {
          id?: string
          trip_id?: string
          destinations?: Json
          generated_at?: string
          generated_by?: string
        }
        Relationships: [
          {
            foreignKeyName: "recommendations_trip_id_fkey"
            columns: ["trip_id"]
            referencedRelation: "trips"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "recommendations_generated_by_fkey"
            columns: ["generated_by"]
            referencedRelation: "users"
            referencedColumns: ["id"]
          },
        ]
      }
      destination_votes: {
        Row: {
          id: string
          recommendation_id: string
          user_id: string
          destination_index: number
          vote_type: Database["public"]["Enums"]["vote_type"]
          created_at: string
        }
        Insert: {
          id?: string
          recommendation_id: string
          user_id: string
          destination_index: number
          vote_type: Database["public"]["Enums"]["vote_type"]
          created_at?: string
        }
        Update: {
          id?: string
          recommendation_id?: string
          user_id?: string
          destination_index?: number
          vote_type?: Database["public"]["Enums"]["vote_type"]
          created_at?: string
        }
        Relationships: [
          {
            foreignKeyName: "destination_votes_recommendation_id_fkey"
            columns: ["recommendation_id"]
            referencedRelation: "recommendations"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "destination_votes_user_id_fkey"
            columns: ["user_id"]
            referencedRelation: "users"
            referencedColumns: ["id"]
          },
        ]
      }
      itineraries: {
        Row: {
          id: string
          trip_id: string
          destination_name: string
          days: Json
          total_cost: number | null
          generated_at: string
          finalized_at: string | null
          finalized_by: string | null
        }
        Insert: {
          id?: string
          trip_id: string
          destination_name: string
          days?: Json
          total_cost?: number | null
          generated_at?: string
          finalized_at?: string | null
          finalized_by?: string | null
        }
        Update: {
          id?: string
          trip_id?: string
          destination_name?: string
          days?: Json
          total_cost?: number | null
          generated_at?: string
          finalized_at?: string | null
          finalized_by?: string | null
        }
        Relationships: [
          {
            foreignKeyName: "itineraries_trip_id_fkey"
            columns: ["trip_id"]
            referencedRelation: "trips"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "itineraries_finalized_by_fkey"
            columns: ["finalized_by"]
            referencedRelation: "users"
            referencedColumns: ["id"]
          },
        ]
      }
    }
    Views: {
      [_ in never]: never
    }
    Functions: {
      [_ in never]: never
    }
    Enums: {
      trip_status:
        | "collecting"
        | "recommending"
        | "voting"
        | "planning"
        | "finalized"
      member_role: "organizer" | "member"
      vote_type: "upvote" | "downvote"
    }
    CompositeTypes: {
      [_ in never]: never
    }
  }
}
