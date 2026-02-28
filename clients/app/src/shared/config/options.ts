import type {
  ActiveDays,
  BudgetMode,
  FeedMode,
  PreferredTime,
  SourceAccessMethod,
  SourceApprovalDecision,
  SourceStatus,
  TimeWindow
} from "../api/types";
import type { FieldOption } from "../ui/fieldTypes";

export const budgetModeOptions: FieldOption<BudgetMode>[] = [
  { value: "budget", label: "Budget Friendly" },
  { value: "moderate", label: "Moderate Spend" },
  { value: "premium", label: "Premium Night Out" },
  { value: "any", label: "Any Budget" }
];

export const activeDaysOptions: FieldOption<ActiveDays>[] = [
  { value: "weekday", label: "Weekdays" },
  { value: "weekend", label: "Weekends" },
  { value: "both", label: "Both" }
];

export const preferredTimeOptions: FieldOption<PreferredTime>[] = [
  { value: "morning", label: "Morning" },
  { value: "afternoon", label: "Afternoon" },
  { value: "evening", label: "Evening" },
  { value: "late_night", label: "Late Night" }
];

export const timeWindowOptions: FieldOption<TimeWindow>[] = [
  { value: "today", label: "Today" },
  { value: "tonight", label: "Tonight" },
  { value: "weekend", label: "This Weekend" },
  { value: "next_7_days", label: "Next 7 Days" }
];

export const feedModeOptions: FieldOption<FeedMode>[] = [
  { value: "solo", label: "Solo" },
  { value: "date", label: "Date Night" },
  { value: "group", label: "Group Plan" }
];

export const sourceStatusFilterOptions: FieldOption<SourceStatus | "all">[] = [
  { value: "all", label: "All" },
  { value: "pending", label: "Pending" },
  { value: "approved", label: "Approved" },
  { value: "rejected", label: "Rejected" },
  { value: "paused", label: "Paused" }
];

export const sourceAccessMethodOptions: FieldOption<SourceAccessMethod>[] = [
  { value: "rss", label: "RSS Feed" },
  { value: "api", label: "API" },
  { value: "ics", label: "Calendar (ICS)" },
  { value: "html_extract", label: "HTML Extraction" },
  { value: "manual", label: "Manual Upload" }
];

export const sourceDecisionOptions: FieldOption<SourceApprovalDecision>[] = [
  { value: "approved", label: "Approve" },
  { value: "rejected", label: "Reject" },
  { value: "needs_manual_review", label: "Manual Review" }
];

export const testNotificationReasonOptions: FieldOption<"high_relevance_time_sensitive" | "scheduled_sync" | "manual_smoke_test">[] = [
  { value: "high_relevance_time_sensitive", label: "High relevance and urgent timing" },
  { value: "scheduled_sync", label: "Regular scheduled check" },
  { value: "manual_smoke_test", label: "Manual smoke test" }
];

export const ingestionReasonOptions: FieldOption<"scheduled_sync" | "manual_retry" | "policy_recheck">[] = [
  { value: "scheduled_sync", label: "Scheduled sync" },
  { value: "manual_retry", label: "Manual retry" },
  { value: "policy_recheck", label: "Policy re-check" }
];

export const suggestedCategoryTags = [
  "events",
  "food",
  "nightlife",
  "sports",
  "sightseeing",
  "museums",
  "outdoors",
  "movies"
];

export const suggestedSubcategoryTags = [
  "indie_music",
  "live_comedy",
  "craft_coffee",
  "rooftop",
  "art_exhibit",
  "family_friendly"
];

export const suggestedAntiPreferenceTags = ["large_crowds", "long_queue", "late_finish", "rain_sensitive"];
