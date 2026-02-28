import { zodResolver } from "@hookform/resolvers/zod";
import { useRouter } from "expo-router";
import { Controller, useForm } from "react-hook-form";
import { ActivityIndicator, Pressable, StyleSheet, Text } from "react-native";

import {
  preferencesFormSchema,
  toPreferenceFormDefaults,
  toPreferenceInput,
  type PreferencesFormValues
} from "../../src/features/preferences/form";
import { useSavePreferencesMutation } from "../../src/features/preferences/api";
import { APIClientError } from "../../src/shared/api/client";
import { FormField } from "../../src/shared/ui/FormField";
import { Screen } from "../../src/shared/ui/Screen";
import { SectionCard } from "../../src/shared/ui/SectionCard";
import { StatusMessage } from "../../src/shared/ui/StatusMessage";

const defaultValues = toPreferenceFormDefaults({
  preferred_categories: ["events", "food", "nightlife"],
  preferred_subcategories: ["indie_music"],
  budget_mode: "moderate",
  preferred_distance_km: 8,
  active_days: "both",
  preferred_times: ["evening"],
  anti_preferences: ["large_crowds"]
});

export default function OnboardingScreen(): JSX.Element {
  const router = useRouter();
  const savePreferences = useSavePreferencesMutation();

  const {
    control,
    handleSubmit,
    formState: { errors }
  } = useForm<PreferencesFormValues>({
    resolver: zodResolver(preferencesFormSchema),
    defaultValues
  });

  const onSubmit = handleSubmit((values) => {
    savePreferences.mutate(toPreferenceInput(values), {
      onSuccess: () => {
        router.replace("/(user)/feed");
      }
    });
  });

  const errorMessage =
    savePreferences.error instanceof APIClientError
      ? `${savePreferences.error.message} (${savePreferences.error.code})`
      : savePreferences.error
        ? "Unable to save preferences."
        : null;

  return (
    <Screen>
      <SectionCard title="Tell AFF what you prefer">
        <Text style={styles.subtitle}>Use comma-separated values for list fields. Example: events, food, nightlife.</Text>

        <Controller
          control={control}
          name="preferred_categories"
          render={({ field: { value, onChange, onBlur } }) => (
            <FormField
              label="Preferred categories"
              value={value}
              onChangeText={onChange}
              onBlur={onBlur}
              error={errors.preferred_categories?.message}
            />
          )}
        />
        <Controller
          control={control}
          name="preferred_subcategories"
          render={({ field: { value, onChange, onBlur } }) => (
            <FormField label="Preferred subcategories" value={value} onChangeText={onChange} onBlur={onBlur} />
          )}
        />
        <Controller
          control={control}
          name="budget_mode"
          render={({ field: { value, onChange, onBlur } }) => (
            <FormField
              label="Budget mode"
              hint="budget | moderate | premium | any"
              value={value}
              onChangeText={onChange}
              onBlur={onBlur}
              autoCapitalize="none"
              error={errors.budget_mode?.message}
            />
          )}
        />
        <Controller
          control={control}
          name="preferred_distance_km"
          render={({ field: { value, onChange, onBlur } }) => (
            <FormField
              label="Preferred distance (km)"
              keyboardType="numeric"
              value={String(value)}
              onChangeText={onChange}
              onBlur={onBlur}
              error={errors.preferred_distance_km?.message}
            />
          )}
        />
        <Controller
          control={control}
          name="active_days"
          render={({ field: { value, onChange, onBlur } }) => (
            <FormField
              label="Active days"
              hint="weekday | weekend | both"
              value={value}
              onChangeText={onChange}
              onBlur={onBlur}
              autoCapitalize="none"
              error={errors.active_days?.message}
            />
          )}
        />
        <Controller
          control={control}
          name="preferred_times"
          render={({ field: { value, onChange, onBlur } }) => (
            <FormField
              label="Preferred times"
              hint="morning, afternoon, evening, late_night"
              value={value}
              onChangeText={onChange}
              onBlur={onBlur}
              error={errors.preferred_times?.message}
            />
          )}
        />
        <Controller
          control={control}
          name="anti_preferences"
          render={({ field: { value, onChange, onBlur } }) => (
            <FormField label="Anti-preferences" value={value} onChangeText={onChange} onBlur={onBlur} />
          )}
        />

        <Pressable accessibilityRole="button" style={styles.primaryBtn} onPress={onSubmit} disabled={savePreferences.isPending}>
          {savePreferences.isPending ? <ActivityIndicator color="#FFFFFF" /> : <Text style={styles.primaryLabel}>Save and Continue</Text>}
        </Pressable>
      </SectionCard>

      {errorMessage ? <StatusMessage tone="error" message={errorMessage} /> : null}
    </Screen>
  );
}

const styles = StyleSheet.create({
  subtitle: {
    color: "#445466",
    lineHeight: 20
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
  }
});
