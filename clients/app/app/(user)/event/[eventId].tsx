import { useLocalSearchParams } from "expo-router";
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from "react-native";

import { useFeedbackMutation } from "../../../src/features/feed/api";
import { useEventDetailQuery } from "../../../src/features/events/api";
import { APIClientError } from "../../../src/shared/api/client";
import type { FeedbackSignal } from "../../../src/shared/api/types";
import { formatDateTimeSg } from "../../../src/shared/time/format";
import { Screen } from "../../../src/shared/ui/Screen";
import { SectionCard } from "../../../src/shared/ui/SectionCard";
import { StatusMessage } from "../../../src/shared/ui/StatusMessage";
import { buttonStyles, textStyles } from "../../../src/shared/ui/theme";

const feedbackSignals: FeedbackSignal[] = ["interested", "not_for_me", "already_knew"];

export default function EventDetailScreen(): JSX.Element {
  const params = useLocalSearchParams<{ eventId?: string }>();
  const eventId = params.eventId ?? "";

  const eventQuery = useEventDetailQuery(eventId);
  const feedbackMutation = useFeedbackMutation();

  const errorMessage =
    eventQuery.error instanceof APIClientError
      ? `${eventQuery.error.message} (${eventQuery.error.code})`
      : eventQuery.error
        ? "Unable to load event detail."
        : null;

  if (eventQuery.isLoading) {
    return (
      <Screen>
        <SectionCard>
          <ActivityIndicator />
        </SectionCard>
      </Screen>
    );
  }

  return (
    <Screen>
      {errorMessage ? <StatusMessage tone="error" message={errorMessage} /> : null}

      {eventQuery.data ? (
        <SectionCard title={eventQuery.data.title}>
          <Text style={styles.meta}>Category: {eventQuery.data.category}</Text>
          {eventQuery.data.subcategory ? <Text style={styles.meta}>Subcategory: {eventQuery.data.subcategory}</Text> : null}
          {eventQuery.data.description ? <Text style={styles.meta}>{eventQuery.data.description}</Text> : null}
          {eventQuery.data.venue_name ? <Text style={styles.meta}>Venue: {eventQuery.data.venue_name}</Text> : null}
          {eventQuery.data.venue_address ? <Text style={styles.meta}>Address: {eventQuery.data.venue_address}</Text> : null}

          <View style={styles.listBlock}>
            <Text style={styles.listTitle}>Occurrences</Text>
            {eventQuery.data.occurrences.map((occurrence) => (
              <Text key={`${occurrence.datetime_start}-${occurrence.timezone}`} style={styles.meta}>
                {formatDateTimeSg(occurrence.datetime_start)} ({occurrence.timezone})
              </Text>
            ))}
          </View>

          <View style={styles.listBlock}>
            <Text style={styles.listTitle}>Source Provenance</Text>
            {eventQuery.data.source_provenance.map((source) => (
              <Text key={source.source_id} style={styles.meta}>
                {source.source_name}: {source.source_url}
              </Text>
            ))}
          </View>

          <View style={styles.row}>
            {feedbackSignals.map((signal) => (
              <Pressable
                key={signal}
                style={styles.feedbackBtn}
                onPress={() =>
                  feedbackMutation.mutate({
                    eventId,
                    payload: {
                      signal,
                      context: {
                        surface: "event_detail"
                      }
                    }
                  })
                }
              >
                <Text style={styles.feedbackLabel}>{signal}</Text>
              </Pressable>
            ))}
          </View>
        </SectionCard>
      ) : null}
    </Screen>
  );
}

const styles = StyleSheet.create({
  meta: {
    ...textStyles.body
  },
  listBlock: {
    gap: 6
  },
  listTitle: {
    ...textStyles.label
  },
  row: {
    flexDirection: "row",
    gap: 10,
    flexWrap: "wrap"
  },
  feedbackBtn: {
    ...buttonStyles.subtleChipBtn
  },
  feedbackLabel: {
    ...buttonStyles.subtleChipLabel,
    textTransform: "capitalize"
  }
});
