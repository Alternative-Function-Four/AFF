import { ActivityIndicator, Pressable, StyleSheet, Text, View } from "react-native";

import { useNotificationsQuery } from "../../src/features/notifications/api";
import { APIClientError } from "../../src/shared/api/client";
import { formatDateTimeSg } from "../../src/shared/time/format";
import { Screen } from "../../src/shared/ui/Screen";
import { SectionCard } from "../../src/shared/ui/SectionCard";
import { StatusMessage } from "../../src/shared/ui/StatusMessage";

export default function NotificationsScreen(): JSX.Element {
  const notifications = useNotificationsQuery(20);

  const queryError =
    notifications.error instanceof APIClientError
      ? `${notifications.error.message} (${notifications.error.code})`
      : notifications.error
        ? "Unable to load notifications."
        : null;

  return (
    <Screen>
      {queryError ? <StatusMessage tone="error" message={queryError} /> : null}

      <SectionCard title="Notification Timeline">
        <Pressable accessibilityRole="button" style={styles.refreshBtn} onPress={() => notifications.refetch()}>
          <Text style={styles.refreshLabel}>Refresh</Text>
        </Pressable>

        {notifications.isLoading ? <ActivityIndicator /> : null}

        {!notifications.isLoading && notifications.data?.items.length === 0 ? (
          <StatusMessage
            tone="info"
            message="No notifications yet. We only send alerts when an event looks highly relevant and timely."
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
  refreshBtn: {
    minHeight: 44,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#B9C6D3",
    backgroundColor: "#FFFFFF",
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: 12
  },
  refreshLabel: {
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
