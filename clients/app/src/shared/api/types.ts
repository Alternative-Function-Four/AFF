export type UserRole = "member" | "admin";

export type BudgetMode = "budget" | "moderate" | "premium" | "any";
export type ActiveDays = "weekday" | "weekend" | "both";
export type PreferredTime = "morning" | "afternoon" | "evening" | "late_night";
export type TimeWindow = "today" | "tonight" | "weekend" | "next_7_days";
export type FeedMode = "solo" | "date" | "group";

export type InteractionSignal =
  | "interested"
  | "not_for_me"
  | "already_knew"
  | "saved"
  | "dismissed"
  | "opened";

export type FeedbackSignal = "interested" | "not_for_me" | "already_knew";

export type SourceAccessMethod = "api" | "rss" | "ics" | "html_extract" | "manual";
export type SourceStatus = "pending" | "approved" | "rejected" | "paused";
export type SourceApprovalDecision = "approved" | "rejected" | "needs_manual_review";

export type NotificationPriority = "low" | "medium" | "high";
export type NotificationStatus = "queued" | "sent" | "suppressed" | "failed";

export interface ErrorEnvelope {
  code: string;
  message: string;
  details: Record<string, unknown>;
  request_id: string;
}

export interface UserSummary {
  id: string;
  display_name: string;
  role?: UserRole | "user";
}

export interface AuthSessionResponse {
  access_token: string;
  token_type: string;
  expires_at: string;
  user: UserSummary;
}

export interface DemoLoginRequest {
  display_name: string;
  persona_seed?: string;
}

export interface PasswordLoginRequest {
  email: string;
  password: string;
}

export interface PreferenceProfileInput {
  preferred_categories: string[];
  preferred_subcategories: string[];
  budget_mode: BudgetMode;
  preferred_distance_km: number;
  home_lat: number;
  home_lng: number;
  home_address: string;
  active_days: ActiveDays;
  preferred_times: PreferredTime[];
  anti_preferences: string[];
}

export interface PreferenceProfile extends PreferenceProfileInput {
  user_id: string;
  updated_at: string;
}

export interface CreatedResponse {
  id: string;
  created_at: string;
}

export interface InteractionCreateRequest {
  event_id: string;
  signal: InteractionSignal;
  context: Record<string, unknown>;
}

export interface Price {
  min?: number | null;
  max?: number | null;
  currency?: string | null;
}

export interface SourceProvenance {
  source_id: string;
  source_name: string;
  source_url: string;
}

export interface FeedItem {
  event_id: string;
  title: string;
  datetime_start: string;
  venue_name: string;
  category: string;
  price?: Price | null;
  relevance_score: number;
  reasons: string[];
  source_provenance: SourceProvenance[];
}

export interface FeedResponse {
  items: FeedItem[];
  coverage_warning: string | null;
  request_id: string;
}

export interface EventOccurrence {
  datetime_start: string;
  datetime_end?: string | null;
  timezone: string;
}

export interface EventDetail {
  event_id: string;
  title: string;
  category: string;
  subcategory?: string | null;
  description?: string | null;
  venue_name?: string | null;
  venue_address?: string | null;
  occurrences: EventOccurrence[];
  source_provenance: SourceProvenance[];
}

export interface EventFeedbackRequest {
  signal: FeedbackSignal;
  context: Record<string, unknown>;
}

export interface NotificationLog {
  id: string;
  event_id: string;
  priority: NotificationPriority;
  title: string;
  body: string;
  status: NotificationStatus;
  sent_at?: string | null;
  created_at: string;
}

export interface NotificationListResponse {
  items: NotificationLog[];
}

export interface TestNotificationRequest {
  event_id: string;
  reason: string;
}

export interface TestNotificationResponse {
  queued: boolean;
  notification_id: string;
}

export interface Source {
  id: string;
  name: string;
  url: string;
  source_type: string;
  access_method: SourceAccessMethod;
  status: SourceStatus;
  policy_risk_score: number;
  quality_score: number;
  crawl_frequency_minutes: number;
  terms_url?: string | null;
  notes?: string | null;
  deleted_at?: string | null;
}

export interface SourceListResponse {
  items: Source[];
}

export interface SourceCreateRequest {
  name: string;
  url: string;
  source_type: string;
  access_method: SourceAccessMethod;
  terms_url?: string;
}

export interface SourceApprovalRequest {
  decision: SourceApprovalDecision;
  policy_risk_score: number;
  quality_score: number;
  notes: string;
}

export interface IngestionRunRequest {
  source_ids: string[];
  reason: string;
}

export interface IngestionRunResponse {
  job_id: string;
  queued_count: number;
}
