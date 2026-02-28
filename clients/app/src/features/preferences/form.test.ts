import { describe, expect, it } from "vitest";

import {
  preferencesFormSchema,
  toPreferenceFormDefaults,
  toPreferenceInput
} from "./form";

describe("preferences form mapping", () => {
  it("converts typed form values to API payload", () => {
    const result = toPreferenceInput({
      preferred_categories: ["events", "food", "nightlife"],
      preferred_subcategories: ["indie_music", "rooftop"],
      budget_mode: "moderate",
      preferred_distance_km: 8,
      home_lat: 1.3005,
      home_lng: 103.8452,
      home_address: "Tiong Bahru, Singapore",
      active_days: "both",
      preferred_times: ["evening", "late_night"],
      anti_preferences: ["large_crowds"]
    });

    expect(result).toEqual({
      preferred_categories: ["events", "food", "nightlife"],
      preferred_subcategories: ["indie_music", "rooftop"],
      budget_mode: "moderate",
      preferred_distance_km: 8,
      home_lat: 1.3005,
      home_lng: 103.8452,
      home_address: "Tiong Bahru, Singapore",
      active_days: "both",
      preferred_times: ["evening", "late_night"],
      anti_preferences: ["large_crowds"]
    });
  });

  it("converts API payload to typed form defaults", () => {
    const result = toPreferenceFormDefaults({
      preferred_categories: ["events", "food"],
      preferred_subcategories: ["indie_music"],
      budget_mode: "budget",
      preferred_distance_km: 3,
      home_lat: 1.312,
      home_lng: 103.902,
      home_address: "Bedok, Singapore",
      active_days: "weekday",
      preferred_times: ["morning", "afternoon"],
      anti_preferences: ["large_crowds", "rain"]
    });

    expect(result).toEqual({
      preferred_categories: ["events", "food"],
      preferred_subcategories: ["indie_music"],
      budget_mode: "budget",
      preferred_distance_km: 3,
      home_lat: 1.312,
      home_lng: 103.902,
      home_address: "Bedok, Singapore",
      active_days: "weekday",
      preferred_times: ["morning", "afternoon"],
      anti_preferences: ["large_crowds", "rain"]
    });
  });

  it("rejects invalid preferred time tokens", () => {
    const parsed = preferencesFormSchema.safeParse({
      preferred_categories: ["events"],
      preferred_subcategories: [],
      budget_mode: "any",
      preferred_distance_km: 5,
      home_lat: 1.3521,
      home_lng: 103.8198,
      home_address: "Singapore",
      active_days: "both",
      preferred_times: ["sunrise"],
      anti_preferences: []
    });

    expect(parsed.success).toBe(false);
    if (!parsed.success) {
      expect(parsed.error.issues[0]?.path).toEqual(["preferred_times", 0]);
    }
  });

  it("rejects empty preferred category selection", () => {
    const parsed = preferencesFormSchema.safeParse({
      preferred_categories: [],
      preferred_subcategories: [],
      budget_mode: "any",
      preferred_distance_km: 5,
      home_lat: 1.3521,
      home_lng: 103.8198,
      home_address: "Singapore",
      active_days: "both",
      preferred_times: ["evening"],
      anti_preferences: []
    });

    expect(parsed.success).toBe(false);
    if (!parsed.success) {
      expect(parsed.error.issues[0]?.path).toEqual(["preferred_categories"]);
    }
  });
});
