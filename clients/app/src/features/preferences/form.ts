import { z } from "zod";

import type { PreferenceProfileInput, PreferredTime } from "../../shared/api/types";

const budgetModes = ["budget", "moderate", "premium", "any"] as const;
const activeDays = ["weekday", "weekend", "both"] as const;
const preferredTimes = ["morning", "afternoon", "evening", "late_night"] as const;

export const preferencesFormSchema = z.object({
  preferred_categories: z.array(z.string().trim().min(1)).min(1, "Choose at least one category."),
  preferred_subcategories: z.array(z.string().trim().min(1)).default([]),
  budget_mode: z.enum(budgetModes),
  preferred_distance_km: z.coerce.number().min(0).max(50),
  home_lat: z.coerce.number().min(1.15).max(1.5),
  home_lng: z.coerce.number().min(103.55).max(104.1),
  home_address: z.string().trim().min(1).max(255),
  active_days: z.enum(activeDays),
  preferred_times: z.array(z.enum(preferredTimes)).min(1, "Choose at least one preferred time."),
  anti_preferences: z.array(z.string().trim().min(1)).default([])
});

export type PreferencesFormValues = z.infer<typeof preferencesFormSchema>;

export function toPreferenceInput(values: PreferencesFormValues): PreferenceProfileInput {
  return {
    preferred_categories: values.preferred_categories,
    preferred_subcategories: values.preferred_subcategories,
    budget_mode: values.budget_mode,
    preferred_distance_km: values.preferred_distance_km,
    home_lat: values.home_lat,
    home_lng: values.home_lng,
    home_address: values.home_address,
    active_days: values.active_days,
    preferred_times: values.preferred_times as PreferredTime[],
    anti_preferences: values.anti_preferences
  };
}

export function toPreferenceFormDefaults(profile: PreferenceProfileInput): PreferencesFormValues {
  return {
    preferred_categories: profile.preferred_categories,
    preferred_subcategories: profile.preferred_subcategories,
    budget_mode: profile.budget_mode,
    preferred_distance_km: profile.preferred_distance_km,
    home_lat: profile.home_lat,
    home_lng: profile.home_lng,
    home_address: profile.home_address,
    active_days: profile.active_days,
    preferred_times: profile.preferred_times,
    anti_preferences: profile.anti_preferences
  };
}
