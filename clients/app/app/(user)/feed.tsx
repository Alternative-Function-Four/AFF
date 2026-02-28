import { useRouter } from "expo-router";
import { useMemo, useState } from "react";
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from "react-native";

import { useFeedbackMutation, useFeedQuery, type FeedParams } from "../../src/features/feed/api";
import { APIClientError } from "../../src/shared/api/client";
import { env } from "../../src/shared/config/env";
import type { FeedbackSignal, TimeWindow, BudgetMode, FeedMode } from "../../src/shared/api/types";
import { useSessionStore } from "../../src/shared/state/session";
import { formatDateTimeSg, formatSgd } from "../../src/shared/time/format";
import { FormField } from "../../src/shared/ui/FormField";
import { Screen } from "../../src/shared/ui/Screen";
import { SectionCard } from "../../src/shared/ui/SectionCard";
import { StatusMessage } from "../../src/shared/ui/StatusMessage";

const feedbackSignals: FeedbackSignal[] = ["interested", "not_for_me", "already_knew"];

const initialFilters: FeedParams = {
  lat: env.defaultLat,
  lng: env.defaultLng,
  time_window: "tonight",
  budget: "any",
  mode: "solo"
};

function isTimeWindow(value: string): value is TimeWindow {
  return value === "today" || value === "tonight" || value === "weekend" || value === "next_7_days";
}

function isBudget(value: string): value is BudgetMode {
  return value === "budget" || value === "moderate" || value === "premium" || value === "any";
}

function isMode(value: string): value is FeedMode {
  return value === "solo" || value === "date" || value === "group";
}

export default function FeedScreen(): JSX.Element {
  const router = useRouter();
  const session = useSessionStore((state) => state.session);

  const [latText, setLatText] = useState(String(initialFilters.lat));
  const [lngText, setLngText] = useState(String(initialFilters.lng));
  const [timeWindowText, setTimeWindowText] = useState<string>(initialFilters.time_window);
  const [budgetText, setBudgetText] = useState<string>(initialFilters.budget);
  const [modeText, setModeText] = useState<string>(initialFilters.mode);

  const filters = useMemo(() => {
    const lat = Number(latText);
    const lng = Number(lngText);
    return {
      lat: Number.isFinite(lat) ? lat : env.defaultLat,
      lng: Number.isFinite(lng) ? lng : env.defaultLng,
      time_window: isTimeWindow(timeWindowText) ? timeWindowText : "tonight",
      budget: isBudget(budgetText) ? budgetText : "any",
      mode: isMode(modeText) ? modeText : "solo"
    } satisfies FeedParams;
  }, [budgetText, latText, lngText, modeText, timeWindowText]);

  const feedQuery = useFeedQuery(filters);
  const feedbackMutation = useFeedbackMutation();

  const errorMessage =
    feedQuery.error instanceof APIClientError
      ? `${feedQuery.error.message} (${feedQuery.error.code})`
      : feedQuery.error
        ? "Unable to load feed."
        : null;

  return (
    <Screen>
      <SectionCard title="Feed Filters">
        <FormField
          label="Latitude"
          value={latText}
          onChangeText={setLatText}
          keyboardType="decimal-pad"
          hint="Singapore default if invalid"
        />
        <FormField
          label="Longitude"
          value={lngText}
          onChangeText={setLngText}
          keyboardType="decimal-pad"
          hint="Singapore default if invalid"
        />
        <FormField
          label="Time window"
          value={timeWindowText}
          onChangeText={setTimeWindowText}
          autoCapitalize="none"
          hint="today | tonight | weekend | next_7_days"
        />
        <FormField
          label="Budget"
          value={budgetText}
          onChangeText={setBudgetText}
          autoCapitalize="none"
          hint="budget | moderate | premium | any"
        />
        <FormField
          label="Mode"
          value={modeText}
          onChangeText={setModeText}
          autoCapitalize="none"
          hint="solo | date | group"
        />
        <Pressable accessibilityRole="button" style={styles.secondaryBtn} onPress={() => feedQuery.refetch()}>
          <Text style={styles.secondaryLabel}>Refresh Feed</Text>
        </Pressable>
      </SectionCard>

      <SectionCard title="Quick Actions">
        <View style={styles.actionsRow}>
          <Pressable style={styles.secondaryBtn} onPress={() => router.push("/(user)/preferences")}>
            <Text style={styles.secondaryLabel}>Preferences</Text>
          </Pressable>
          <Pressable style={styles.secondaryBtn} onPress={() => router.push("/(user)/notifications")}>
            <Text style={styles.secondaryLabel}>Notifications</Text>
          </Pressable>
        </View>
        {env.enableAdmin && session?.user.role === "admin" ? (
          <Pressable style={styles.secondaryBtn} onPress={() => router.push("/admin/sources")}>
            <Text style={styles.secondaryLabel}>Admin Sources</Text>
          </Pressable>
        ) : null}
      </SectionCard>

      {feedQuery.isLoading ? (
        <SectionCard>
          <ActivityIndicator />
        </SectionCard>
      ) : null}

      {errorMessage ? <StatusMessage tone="error" message={errorMessage} /> : null}

      {feedQuery.data?.coverage_warning ? <StatusMessage tone="info" message={feedQuery.data.coverage_warning} /> : null}

      {feedQuery.data?.items.map((item) => (
        <SectionCard key={item.event_id} title={item.title}>
          <Text style={styles.meta}>{formatDateTimeSg(item.datetime_start)} · {item.venue_name || "Venue TBD"}</Text>
          <Text style={styles.meta}>{item.category} · {formatSgd(item.price?.min, item.price?.max)}</Text>
          <Text style={styles.meta}>Score: {item.relevance_score.toFixed(2)}</Text>
          <Text style={styles.meta}>Reason: {item.reasons.join("; ")}</Text>
          <Text style={styles.meta}>Sources: {item.source_provenance.map((s) => s.source_name).join(", ")}</Text>

          <Pressable style={styles.primaryBtn} onPress={() => router.push(`/(user)/event/${item.event_id}`)}>
            <Text style={styles.primaryLabel}>View Detail</Text>
          </Pressable>

          <View style={styles.actionsRow}>
            {feedbackSignals.map((signal) => (
              <Pressable
                key={signal}
                style={styles.feedbackBtn}
                disabled={feedbackMutation.isPending}
                onPress={() =>
                  feedbackMutation.mutate({
                    eventId: item.event_id,
                    payload: {
                      signal,
                      context: {
                        surface: "feed"
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
      ))}
    </Screen>
  );
}

const styles = StyleSheet.create({
  meta: {
    color: "#3D5064",
    lineHeight: 19
  },
  actionsRow: {
    flexDirection: "row",
    gap: 10,
    flexWrap: "wrap"
  },
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
    flexGrow: 1,
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
  feedbackBtn: {
    minHeight: 44,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#91A0AF",
    backgroundColor: "#FFFFFF",
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: 10
  },
  feedbackLabel: {
    fontSize: 12,
    color: "#1A3149",
    fontWeight: "600"
  }
});
