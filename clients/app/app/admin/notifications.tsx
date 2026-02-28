import { useEffect, useMemo, useState } from "react";
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from "react-native";

import { useFeedQuery } from "../../src/features/feed/api";
import { useNotificationsQuery, useTestNotificationMutation } from "../../src/features/notifications/api";
import { APIClientError } from "../../src/shared/api/client";
import { env } from "../../src/shared/config/env";
import { testNotificationReasonOptions } from "../../src/shared/config/options";
import { trackEvent } from "../../src/shared/telemetry/events";
import { formatDateTimeSg } from "../../src/shared/time/format";
import { FormField } from "../../src/shared/ui/FormField";
import type { FieldOption } from "../../src/shared/ui/fieldTypes";
import { Screen } from "../../src/shared/ui/Screen";
import { SectionCard } from "../../src/shared/ui/SectionCard";
import { SingleSelectField } from "../../src/shared/ui/SingleSelectField";
import { StatusMessage } from "../../src/shared/ui/StatusMessage";

type NotificationReason = "high_relevance_time_sensitive" | "scheduled_sync" | "manual_smoke_test";

export default function AdminNotificationsScreen(): JSX.Element {
  const [selectedEventId, setSelectedEventId] = useState("");
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [manualEventId, setManualEventId] = useState("");
  const [reason, setReason] = useState<NotificationReason>("high_relevance_time_sensitive");

  const notifications = useNotificationsQuery(20);
  const feedQuery = useFeedQuery({
    lat: env.defaultLat,
    lng: env.defaultLng,
    time_window: "tonight",
    budget: "any",
    mode: "solo"
  });
  const testMutation = useTestNotificationMutation();

  const eventOptions = useMemo<FieldOption<string>[]>(() => {
    const fromFeed =
      feedQuery.data?.items.map((item) => ({
        value: item.event_id,
        label: item.title,
        description: `${formatDateTimeSg(item.datetime_start)} · ${item.venue_name || "Venue TBD"}`
      })) ?? [];

    if (fromFeed.length > 0) {
      return fromFeed;
    }

    const deduped = new Map<string, FieldOption<string>>();
    for (const item of notifications.data?.items ?? []) {
      if (!deduped.has(item.event_id)) {
        deduped.set(item.event_id, {
          value: item.event_id,
          label: item.title,
          description: `Last seen ${formatDateTimeSg(item.created_at)}`
        });
      }
    }
    return Array.from(deduped.values());
  }, [feedQuery.data?.items, notifications.data?.items]);

  useEffect(() => {
    const firstOption = eventOptions[0];
    if (!selectedEventId && firstOption) {
      setSelectedEventId(firstOption.value);
    }
  }, [eventOptions, selectedEventId]);

  const chosenEventId = showAdvanced && manualEventId.trim().length > 0 ? manualEventId.trim() : selectedEventId;

  const queryError =
    notifications.error instanceof APIClientError
      ? `${notifications.error.message} (${notifications.error.code})`
      : notifications.error
        ? "Unable to load notification history."
        : null;

  const mutationError =
    testMutation.error instanceof APIClientError
      ? `${testMutation.error.message} (${testMutation.error.code})`
      : testMutation.error
        ? "Unable to trigger test notification."
        : null;

  return (
    <Screen>
      <SectionCard title="Trigger Test Notification">
        {feedQuery.isLoading ? <ActivityIndicator /> : null}
        {eventOptions.length === 0 ? (
          <StatusMessage
            tone="info"
            message="No candidate events are available yet. Refresh feed or wait for more event data."
          />
        ) : (
          <SingleSelectField
            label="Event"
            options={eventOptions}
            value={selectedEventId}
            onChange={(nextValue) => {
              setSelectedEventId(nextValue);
              trackEvent("notification_test_event_selected", {
                surface: "admin_web",
                source: "selector"
              });
            }}
          />
        )}

        <SingleSelectField label="Reason" options={testNotificationReasonOptions} value={reason} onChange={setReason} />

        <Pressable
          accessibilityRole="button"
          style={styles.secondaryBtn}
          onPress={() => {
            const nextValue = !showAdvanced;
            setShowAdvanced(nextValue);
            trackEvent("ui_advanced_mode_toggled", {
              surface: "admin_web",
              enabled: nextValue
            });
          }}
        >
          <Text style={styles.secondaryLabel}>{showAdvanced ? "Hide advanced" : "Show advanced"}</Text>
        </Pressable>

        {showAdvanced ? (
          <FormField
            label="Manual event ID (advanced)"
            hint="Only use this for edge-case troubleshooting."
            value={manualEventId}
            onChangeText={setManualEventId}
            autoCapitalize="none"
            autoCorrect={false}
          />
        ) : null}

        <Pressable
          accessibilityRole="button"
          style={styles.primaryBtn}
          disabled={testMutation.isPending || chosenEventId.length === 0}
          onPress={() =>
            testMutation.mutate({
              event_id: chosenEventId,
              reason
            })
          }
        >
          {testMutation.isPending ? <ActivityIndicator color="#FFFFFF" /> : <Text style={styles.primaryLabel}>Trigger</Text>}
        </Pressable>

        {testMutation.data ? (
          <StatusMessage
            tone={testMutation.data.queued ? "success" : "info"}
            message={
              testMutation.data.queued
                ? `Queued notification ${testMutation.data.notification_id}`
                : `Suppressed notification ${testMutation.data.notification_id}`
            }
          />
        ) : null}
      </SectionCard>

      {queryError ? <StatusMessage tone="error" message={queryError} /> : null}
      {mutationError ? <StatusMessage tone="error" message={mutationError} /> : null}

      <SectionCard title="Recent Notification Timeline">
        {notifications.isLoading ? <ActivityIndicator /> : null}
        <Pressable accessibilityRole="button" style={styles.secondaryBtn} onPress={() => notifications.refetch()}>
          <Text style={styles.secondaryLabel}>Refresh Timeline</Text>
        </Pressable>
        {notifications.data?.items.map((item) => (
          <View key={item.id} style={styles.itemRow}>
            <Text style={styles.title}>{item.title}</Text>
            <Text style={styles.meta}>{item.status.toUpperCase()} · {item.priority.toUpperCase()}</Text>
            <Text style={styles.meta}>{formatDateTimeSg(item.created_at)}</Text>
          </View>
        ))}
      </SectionCard>
    </Screen>
  );
}

const styles = StyleSheet.create({
  primaryBtn: {
    minHeight: 44,
    borderRadius: 8,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#1E4FDB"
  },
  primaryLabel: {
    color: "#FFFFFF",
    fontWeight: "700"
  },
  secondaryBtn: {
    minHeight: 44,
    borderRadius: 8,
    alignItems: "center",
    justifyContent: "center",
    borderWidth: 1,
    borderColor: "#B9C6D3",
    backgroundColor: "#FFFFFF",
    paddingHorizontal: 12
  },
  secondaryLabel: {
    color: "#223B53",
    fontWeight: "600"
  },
  itemRow: {
    borderTopWidth: 1,
    borderTopColor: "#E3E8EF",
    paddingTop: 10,
    gap: 4
  },
  title: {
    fontWeight: "700",
    color: "#162B40"
  },
  meta: {
    color: "#3D5064"
  }
});
