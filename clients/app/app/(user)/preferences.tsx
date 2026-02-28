import { zodResolver } from "@hookform/resolvers/zod";
import { Controller, useForm } from "react-hook-form";
import { useEffect } from "react";
import { ActivityIndicator, Pressable, StyleSheet, Text } from "react-native";

import {
  activeDaysOptions,
  budgetModeOptions,
  preferredTimeOptions,
  suggestedAntiPreferenceTags,
  suggestedCategoryTags,
  suggestedSubcategoryTags
} from "../../src/shared/config/options";
import {
  preferencesFormSchema,
  toPreferenceFormDefaults,
  toPreferenceInput,
  type PreferencesFormValues
} from "../../src/features/preferences/form";
import { usePreferencesQuery, useSavePreferencesMutation } from "../../src/features/preferences/api";
import { APIClientError } from "../../src/shared/api/client";
import { FormField } from "../../src/shared/ui/FormField";
import { MultiSelectChipsField } from "../../src/shared/ui/MultiSelectChipsField";
import { Screen } from "../../src/shared/ui/Screen";
import { SectionCard } from "../../src/shared/ui/SectionCard";
import { SegmentedControlField } from "../../src/shared/ui/SegmentedControlField";
import { StatusMessage } from "../../src/shared/ui/StatusMessage";
import { TagInputField } from "../../src/shared/ui/TagInputField";

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
      preferred_categories: [],
      preferred_subcategories: [],
      budget_mode: "moderate",
      preferred_distance_km: 8,
      active_days: "both",
      preferred_times: ["evening"],
      anti_preferences: []
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
        ? "We couldn't load your preferences."
        : null;

  const mutationError =
    savePreferences.error instanceof APIClientError
      ? `${savePreferences.error.message} (${savePreferences.error.code})`
      : savePreferences.error
        ? "We couldn't save your changes."
        : null;

  return (
    <Screen>
      <SectionCard title="Preferences">
        <Text style={styles.subtitle}>Update your tastes anytime. We'll use this on your next feed refresh.</Text>
        {preferencesQuery.isLoading ? <ActivityIndicator /> : null}

        <Controller
          control={control}
          name="preferred_categories"
          render={({ field: { value, onChange } }) => (
            <TagInputField
              label="Favorite categories"
              values={value}
              onChange={onChange}
              suggestions={suggestedCategoryTags}
              error={errors.preferred_categories?.message}
            />
          )}
        />
        <Controller
          control={control}
          name="preferred_subcategories"
          render={({ field: { value, onChange } }) => (
            <TagInputField label="Specific interests" values={value} onChange={onChange} suggestions={suggestedSubcategoryTags} />
          )}
        />
        <Controller
          control={control}
          name="budget_mode"
          render={({ field: { value, onChange } }) => (
            <SegmentedControlField label="Budget preference" options={budgetModeOptions} value={value} onChange={onChange} />
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
              hint="Set the maximum travel distance."
              error={errors.preferred_distance_km?.message}
            />
          )}
        />
        <Controller
          control={control}
          name="active_days"
          render={({ field: { value, onChange } }) => (
            <SegmentedControlField label="Active days" options={activeDaysOptions} value={value} onChange={onChange} />
          )}
        />
        <Controller
          control={control}
          name="preferred_times"
          render={({ field: { value, onChange } }) => (
            <MultiSelectChipsField
              label="Preferred times"
              options={preferredTimeOptions}
              values={value}
              onChange={onChange}
              error={errors.preferred_times?.message}
            />
          )}
        />
        <Controller
          control={control}
          name="anti_preferences"
          render={({ field: { value, onChange } }) => (
            <TagInputField
              label="Avoid these"
              values={value}
              onChange={onChange}
              suggestions={suggestedAntiPreferenceTags}
              hint="Optional. Tap a selected item to remove it."
            />
          )}
        />

        <Pressable accessibilityRole="button" style={styles.primaryBtn} onPress={onSubmit} disabled={savePreferences.isPending}>
          {savePreferences.isPending ? <ActivityIndicator color="#FFFFFF" /> : <Text style={styles.primaryLabel}>Save Changes</Text>}
        </Pressable>
      </SectionCard>

      {queryError ? <StatusMessage tone="error" message={queryError} /> : null}
      {mutationError ? <StatusMessage tone="error" message={mutationError} /> : null}
      {savePreferences.isSuccess ? <StatusMessage tone="success" message="Preferences saved." /> : null}
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
