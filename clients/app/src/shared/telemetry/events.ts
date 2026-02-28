export type TelemetryEventName =
  | "auth_demo_login_started"
  | "auth_demo_login_succeeded"
  | "feed_request_started"
  | "feed_request_succeeded"
  | "feed_feedback_submitted"
  | "feed_feedback_succeeded"
  | "notification_test_triggered"
  | "admin_source_approved"
  | "admin_ingestion_run_triggered";

export type TelemetryPayload = {
  timestamp: string;
  user_id_hash?: string;
  request_id?: string;
  surface?: "mobile" | "admin_web";
  network_status?: string;
  duration_ms?: number;
  [key: string]: unknown;
};

export function trackEvent(name: TelemetryEventName, payload: Omit<TelemetryPayload, "timestamp"> = {}): void {
  const event: TelemetryPayload = {
    timestamp: new Date().toISOString(),
    ...payload
  };
  // Placeholder pipeline; swap this with analytics provider when ready.
  console.info(`[telemetry] ${name}`, event);
}
