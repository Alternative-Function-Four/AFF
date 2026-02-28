import type { BudgetMode, FeedMode, TimeWindow } from "./types";

export const queryKeys = {
  preferences: ["preferences"] as const,
  feed: (params: { lat: number; lng: number; time_window: TimeWindow; budget: BudgetMode; mode: FeedMode }) =>
    ["feed", params.lat, params.lng, params.time_window, params.budget, params.mode] as const,
  event: (eventId: string) => ["event", eventId] as const,
  notifications: (limit: number) => ["notifications", limit] as const,
  adminSources: (status: string) => ["admin", "sources", status] as const
};
