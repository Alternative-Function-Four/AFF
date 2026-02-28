import { useRouter } from "expo-router";
import { useEffect, useMemo, useState } from "react";
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from "react-native";

import { useFeedbackMutation, useFeedQuery, type FeedParams } from "../../src/features/feed/api";
import { usePreferencesQuery, useSavePreferencesMutation } from "../../src/features/preferences/api";
import { APIClientError } from "../../src/shared/api/client";
import { env } from "../../src/shared/config/env";
import { budgetModeOptions, feedModeOptions, timeWindowOptions } from "../../src/shared/config/options";
import type { FeedbackSignal, TimeWindow, BudgetMode, FeedMode } from "../../src/shared/api/types";
import { useSessionStore } from "../../src/shared/state/session";
import { trackEvent } from "../../src/shared/telemetry/events";
import { formatDateTimeSg, formatSgd } from "../../src/shared/time/format";
import { SingaporeLocationPickerField } from "../../src/shared/ui/SingaporeLocationPickerField";
import { Screen } from "../../src/shared/ui/Screen";
import { SectionCard } from "../../src/shared/ui/SectionCard";
import { SegmentedControlField } from "../../src/shared/ui/SegmentedControlField";
import { SingleSelectField } from "../../src/shared/ui/SingleSelectField";
import { StatusMessage } from "../../src/shared/ui/StatusMessage";
import { buttonStyles, textStyles } from "../../src/shared/ui/theme";

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
  const preferencesQuery = usePreferencesQuery();
  const savePreferences = useSavePreferencesMutation();

  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);
  const [location, setLocation] = useState({
    lat: initialFilters.lat,
    lng: initialFilters.lng,
    address: "Singapore"
  });
  const [locationDirty, setLocationDirty] = useState(false);
  const [timeWindowText, setTimeWindowText] = useState<TimeWindow>(initialFilters.time_window);
  const [budgetText, setBudgetText] = useState<BudgetMode>(initialFilters.budget);
  const [modeText, setModeText] = useState<FeedMode>(initialFilters.mode);

  useEffect(() => {
    if (!preferencesQuery.data || locationDirty) {
      return;
    }

    setLocation({
      lat: preferencesQuery.data.home_lat,
      lng: preferencesQuery.data.home_lng,
      address: preferencesQuery.data.home_address
    });
  }, [locationDirty, preferencesQuery.data]);

  const filters = useMemo(() => {
    return {
      lat: location.lat,
      lng: location.lng,
      time_window: isTimeWindow(timeWindowText) ? timeWindowText : "tonight",
      budget: isBudget(budgetText) ? budgetText : "any",
      mode: isMode(modeText) ? modeText : "solo"
    } satisfies FeedParams;
  }, [budgetText, location.lat, location.lng, modeText, timeWindowText]);

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
        <SingleSelectField
          label="When are you planning?"
          options={timeWindowOptions}
          value={timeWindowText}
          onChange={(next) => {
            setTimeWindowText(next);
            trackEvent("ui_selector_used", {
              surface: "mobile",
              selector: "feed_time_window",
              value: next
            });
          }}
        />
        <SegmentedControlField
          label="Budget"
          options={budgetModeOptions}
          value={budgetText}
          onChange={(next) => {
            setBudgetText(next);
            trackEvent("ui_selector_used", {
              surface: "mobile",
              selector: "feed_budget",
              value: next
            });
          }}
        />
        <SegmentedControlField
          label="Plan type"
          options={feedModeOptions}
          value={modeText}
          onChange={(next) => {
            setModeText(next);
            trackEvent("ui_selector_used", {
              surface: "mobile",
              selector: "feed_mode",
              value: next
            });
          }}
        />

        <Pressable
          accessibilityRole="button"
          style={styles.secondaryBtn}
          onPress={() => {
            const nextValue = !showAdvancedFilters;
            setShowAdvancedFilters(nextValue);
            trackEvent("ui_advanced_mode_toggled", {
              surface: "mobile",
              enabled: nextValue
            });
          }}
        >
          <Text style={styles.secondaryLabel}>{showAdvancedFilters ? "Hide advanced location filters" : "Show advanced location filters"}</Text>
        </Pressable>

        {showAdvancedFilters ? (
          <>
            <SingaporeLocationPickerField
              label="Location"
              value={location}
              onChange={(next) => {
                setLocation(next);
                setLocationDirty(true);
              }}
              hint="This updates your feed filters immediately. Save to tie this location to your account."
            />
            <View style={styles.actionsRow}>
              <Pressable
                accessibilityRole="button"
                style={styles.secondaryBtn}
                onPress={() => {
                  if (!preferencesQuery.data) {
                    return;
                  }
                  setLocation({
                    lat: preferencesQuery.data.home_lat,
                    lng: preferencesQuery.data.home_lng,
                    address: preferencesQuery.data.home_address
                  });
                  setLocationDirty(false);
                }}
                disabled={!preferencesQuery.data}
              >
                <Text style={styles.secondaryLabel}>Use Saved Home Location</Text>
              </Pressable>
              <Pressable
                accessibilityRole="button"
                style={styles.primaryBtn}
                onPress={() => {
                  if (!preferencesQuery.data) {
                    return;
                  }

                  const profile = preferencesQuery.data;
                  savePreferences.mutate({
                    preferred_categories: profile.preferred_categories,
                    preferred_subcategories: profile.preferred_subcategories,
                    budget_mode: profile.budget_mode,
                    preferred_distance_km: profile.preferred_distance_km,
                    home_lat: location.lat,
                    home_lng: location.lng,
                    home_address: location.address,
                    active_days: profile.active_days,
                    preferred_times: profile.preferred_times,
                    anti_preferences: profile.anti_preferences
                  });
                }}
                disabled={savePreferences.isPending || !preferencesQuery.data}
              >
                {savePreferences.isPending ? (
                  <ActivityIndicator color="#FFFFFF" />
                ) : (
                  <Text style={styles.primaryLabel}>Save As Home Location</Text>
                )}
              </Pressable>
            </View>
          </>
        ) : null}

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
      {savePreferences.isSuccess ? <StatusMessage tone="success" message="Home location saved to your account." /> : null}
      {savePreferences.error ? <StatusMessage tone="error" message="Unable to save home location." /> : null}

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
    ...textStyles.body
  },
  actionsRow: {
    flexDirection: "row",
    gap: 10,
    flexWrap: "wrap"
  },
  primaryBtn: {
    ...buttonStyles.primaryBtn
  },
  primaryLabel: {
    ...buttonStyles.primaryLabel
  },
  secondaryBtn: {
    ...buttonStyles.secondaryBtn,
    flexGrow: 1,
    minWidth: 132
  },
  secondaryLabel: {
    ...buttonStyles.secondaryLabel
  },
  feedbackBtn: {
    ...buttonStyles.subtleChipBtn
  },
  feedbackLabel: {
    ...buttonStyles.subtleChipLabel,
    textTransform: "capitalize"
  }
});
