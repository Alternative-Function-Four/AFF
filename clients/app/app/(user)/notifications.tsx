import { useState } from "react";
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from "react-native";

import { useNotificationsQuery, useTestNotificationMutation } from "../../src/features/notifications/api";
import { APIClientError } from "../../src/shared/api/client";
import { formatDateTimeSg } from "../../src/shared/time/format";
import { FormField } from "../../src/shared/ui/FormField";
import { Screen } from "../../src/shared/ui/Screen";
import { SectionCard } from "../../src/shared/ui/SectionCard";
import { StatusMessage } from "../../src/shared/ui/StatusMessage";

export default function NotificationsScreen(): JSX.Element {
  const [eventId, setEventId] = useState("");
  const [reason, setReason] = useState("high_relevance_time_sensitive");

  const notifications = useNotificationsQuery(20);
  const testMutation = useTestNotificationMutation();

  const queryError =
    notifications.error instanceof APIClientError
      ? `${notifications.error.message} (${notifications.error.code})`
      : notifications.error
        ? "Unable to load notifications."
        : null;

  const mutationError =
    testMutation.error instanceof APIClientError
      ? `${testMutation.error.message} (${testMutation.error.code})`
      : testMutation.error
        ? "Unable to trigger notification."
        : null;

  return (
    <Screen>
      <SectionCard title="Trigger Test Notification">
        <FormField
          label="Event ID"
          hint="Use an event id from feed/event detail"
          value={eventId}
          onChangeText={setEventId}
          autoCapitalize="none"
          autoCorrect={false}
        />
        <FormField label="Reason" value={reason} onChangeText={setReason} autoCapitalize="none" autoCorrect={false} />

        <Pressable
          accessibilityRole="button"
          style={styles.primaryBtn}
          disabled={testMutation.isPending || eventId.trim().length === 0}
          onPress={() =>
            testMutation.mutate({
              event_id: eventId.trim(),
              reason: reason.trim().length ? reason.trim() : "high_relevance_time_sensitive"
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

      <SectionCard title="Notification Timeline">
        {notifications.isLoading ? <ActivityIndicator /> : null}

        {!notifications.isLoading && notifications.data?.items.length === 0 ? (
          <StatusMessage
            tone="info"
            message="No notifications yet. You may be outside eligibility, in quiet hours, or rate-limited by daily quota."
          />
        ) : null}

        {notifications.data?.items.map((item) => (
          <View key={item.id} style={styles.itemRow}>
            <Text style={styles.title}>{item.title}</Text>
            <Text style={styles.meta}>{item.status.toUpperCase()} · {item.priority.toUpperCase()}</Text>
            <Text style={styles.meta}>{formatDateTimeSg(item.created_at)}</Text>
            <Text style={styles.meta}>{item.body}</Text>
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
