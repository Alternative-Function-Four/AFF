import { zodResolver } from "@hookform/resolvers/zod";
import { Controller, useForm } from "react-hook-form";
import { useEffect } from "react";
import { ActivityIndicator, Pressable, StyleSheet, Text } from "react-native";

import {
  preferencesFormSchema,
  toPreferenceFormDefaults,
  toPreferenceInput,
  type PreferencesFormValues
} from "../../src/features/preferences/form";
import { usePreferencesQuery, useSavePreferencesMutation } from "../../src/features/preferences/api";
import { APIClientError } from "../../src/shared/api/client";
import { FormField } from "../../src/shared/ui/FormField";
import { Screen } from "../../src/shared/ui/Screen";
import { SectionCard } from "../../src/shared/ui/SectionCard";
import { StatusMessage } from "../../src/shared/ui/StatusMessage";

export default function PreferencesScreen(): JSX.Element {
  const preferencesQuery = usePreferencesQuery();
  const savePreferences = useSavePreferencesMutation();

  const {
    control,
    reset,
    handleSubmit,
    formState: { errors }
  } = useForm<PreferencesFormValues>({
    resolver: zodResolver(preferencesFormSchema),
    defaultValues: {
      preferred_categories: "",
      preferred_subcategories: "",
      budget_mode: "moderate",
      preferred_distance_km: 8,
      active_days: "both",
      preferred_times: "evening",
      anti_preferences: ""
    }
  });

  useEffect(() => {
    if (preferencesQuery.data) {
      reset(toPreferenceFormDefaults(preferencesQuery.data));
    }
  }, [preferencesQuery.data, reset]);

  const onSubmit = handleSubmit((values) => {
    savePreferences.mutate(toPreferenceInput(values));
  });

  const queryError =
    preferencesQuery.error instanceof APIClientError
      ? `${preferencesQuery.error.message} (${preferencesQuery.error.code})`
      : preferencesQuery.error
        ? "Unable to load preferences."
        : null;

  const mutationError =
    savePreferences.error instanceof APIClientError
      ? `${savePreferences.error.message} (${savePreferences.error.code})`
      : savePreferences.error
        ? "Unable to save preferences."
        : null;

  return (
    <Screen>
      <SectionCard title="Preferences">
        {preferencesQuery.isLoading ? <ActivityIndicator /> : null}

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
          {savePreferences.isPending ? <ActivityIndicator color="#FFFFFF" /> : <Text style={styles.primaryLabel}>Save Changes</Text>}
        </Pressable>
      </SectionCard>

      {queryError ? <StatusMessage tone="error" message={queryError} /> : null}
      {mutationError ? <StatusMessage tone="error" message={mutationError} /> : null}
      {savePreferences.isSuccess ? <StatusMessage tone="success" message="Preferences saved with optimistic update." /> : null}
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
  }
});
