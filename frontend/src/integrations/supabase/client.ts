// This file is automatically generated. Do not edit it directly.
import { createClient } from '@supabase/supabase-js';
import type { Database } from './types';

const SUPABASE_URL = "https://ikrlfllqwyxldxjellwc.supabase.co";
const SUPABASE_PUBLISHABLE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlrcmxmbGxxd3l4bGR4amVsbHdjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM0NDQ3NjIsImV4cCI6MjA2OTAyMDc2Mn0.m6wxJdnpQOG-vO3_EJDz_PwGBc-jMrjBG6BvqA1yy2k";

// Import the supabase client like this:
// import { supabase } from "@/integrations/supabase/client";

export const supabase = createClient<Database>(SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY, {
  auth: {
    storage: localStorage,
    persistSession: true,
    autoRefreshToken: true,
  }
});