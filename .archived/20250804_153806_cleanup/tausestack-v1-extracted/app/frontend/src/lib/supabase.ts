import { createClient } from '@supabase/supabase-js'

// Variables de entorno con fallbacks para evitar errores en SSR
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || 'https://vjoxmprmcbkmhwmbniaz.supabase.co'
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZqb3htcHJtY2JrbWh3bWJuaWF6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTE1NzM4NzQsImV4cCI6MjA2NzE0OTg3NH0.bY4FrlKtDK2TnMt7hOC5_KpIuoHwqJLOYkB-bWs_Wd8'

// Debug para ver qué valores recibe Next.js
console.log('🔍 DEBUG ENV:', {
  url: supabaseUrl,
  urlLength: supabaseUrl?.length,
  key: supabaseAnonKey ? supabaseAnonKey.substring(0, 20) + '...' : 'undefined',
  keyLength: supabaseAnonKey?.length,
  hasUrl: !!supabaseUrl,
  hasKey: !!supabaseAnonKey,
  fromEnv: !!process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY,
  envKey: process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ? process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY.substring(0, 20) + '...' : 'undefined',
  envKeyLength: process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY?.length,
  lastChars: supabaseAnonKey ? supabaseAnonKey.substring(supabaseAnonKey.length - 10) : 'undefined'
})

export const supabase = createClient(supabaseUrl, supabaseAnonKey, {
  auth: {
    autoRefreshToken: true,
    persistSession: true,
    detectSessionInUrl: true
  }
})

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
      tenants: {
        Row: {
          id: string
          name: string
          plan: string
          status: string
          created_at: string
          updated_at: string
          config: Json
        }
        Insert: {
          id?: string
          name: string
          plan?: string
          status?: string
          created_at?: string
          updated_at?: string
          config?: Json
        }
        Update: {
          id?: string
          name?: string
          plan?: string
          status?: string
          created_at?: string
          updated_at?: string
          config?: Json
        }
      }
      users: {
        Row: {
          id: string
          email: string
          name: string | null
          role: string
          tenant_id: string | null
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          email: string
          name?: string | null
          role?: string
          tenant_id?: string | null
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          email?: string
          name?: string | null
          role?: string
          tenant_id?: string | null
          created_at?: string
          updated_at?: string
        }
      }
    }
    Views: {
      [_ in never]: never
    }
    Functions: {
      [_ in never]: never
    }
    Enums: {
      [_ in never]: never
    }
  }
} 