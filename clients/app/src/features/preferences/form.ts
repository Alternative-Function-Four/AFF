import { z } from "zod";

import type { ActiveDays, BudgetMode, PreferenceProfileInput, PreferredTime } from "../../shared/api/types";

const budgetModes = ["budget", "moderate", "premium", "any"] as const;
const activeDays = ["weekday", "weekend", "both"] as const;
const preferredTimes = ["morning", "afternoon", "evening", "late_night"] as const;

export const preferencesFormSchema = z.object({
  preferred_categories: z.string().trim().min(1, "Enter at least one category."),
  preferred_subcategories: z.string().trim().default(""),
  budget_mode: z.enum(budgetModes),
  preferred_distance_km: z.coerce.number().min(0).max(50),
  active_days: z.enum(activeDays),
  preferred_times: z
    .string()
    .trim()
    .min(1, "Enter at least one preferred time.")
    .refine(
      (value) => {
        const values = splitList(value);
        return values.length > 0 && values.every((item) => preferredTimes.includes(item as PreferredTime));
      },
      "Use comma-separated values from: morning, afternoon, evening, late_night."
    ),
  anti_preferences: z.string().trim().default("")
});

export type PreferencesFormValues = z.infer<typeof preferencesFormSchema>;

function splitList(value: string): string[] {
  return value
    .split(",")
    .map((item) => item.trim())
    .filter((item) => item.length > 0);
}

export function toPreferenceInput(values: PreferencesFormValues): PreferenceProfileInput {
  return {
    preferred_categories: splitList(values.preferred_categories),
    preferred_subcategories: splitList(values.preferred_subcategories),
    budget_mode: values.budget_mode,
    preferred_distance_km: values.preferred_distance_km,
    active_days: values.active_days,
    preferred_times: splitList(values.preferred_times) as PreferredTime[],
    anti_preferences: splitList(values.anti_preferences)
  };
}

export function toPreferenceFormDefaults(profile: PreferenceProfileInput): PreferencesFormValues {
  return {
    preferred_categories: profile.preferred_categories.join(", "),
    preferred_subcategories: profile.preferred_subcategories.join(", "),
    budget_mode: profile.budget_mode,
    preferred_distance_km: profile.preferred_distance_km,
    active_days: profile.active_days,
    preferred_times: profile.preferred_times.join(", "),
    anti_preferences: profile.anti_preferences.join(", ")
  };
}
