import { ActivityIndicator, Pressable, StyleSheet, Text, View } from "react-native";

import { useNotificationsQuery } from "../../src/features/notifications/api";
import { APIClientError } from "../../src/shared/api/client";
import { formatDateTimeSg } from "../../src/shared/time/format";
import { Screen } from "../../src/shared/ui/Screen";
import { SectionCard } from "../../src/shared/ui/SectionCard";
import { StatusMessage } from "../../src/shared/ui/StatusMessage";
import { buttonStyles, palette, textStyles, typography } from "../../src/shared/ui/theme";

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
    ...buttonStyles.secondaryBtn
  },
  refreshLabel: {
    ...buttonStyles.secondaryLabel
  },
  itemRow: {
    borderTopWidth: 1,
    borderTopColor: palette.border,
    paddingTop: 12,
    gap: 6
  },
  title: {
    color: palette.textPrimary,
    fontFamily: typography.body,
    fontWeight: "700"
  },
  meta: {
    ...textStyles.body
  }
});
