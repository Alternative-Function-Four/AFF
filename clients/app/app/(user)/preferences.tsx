import { zodResolver } from "@hookform/resolvers/zod";
import { Controller, useForm, useWatch } from "react-hook-form";
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
import { SingaporeLocationPickerField } from "../../src/shared/ui/SingaporeLocationPickerField";
import { buttonStyles, textStyles } from "../../src/shared/ui/theme";

export default function PreferencesScreen(): JSX.Element {
  const preferencesQuery = usePreferencesQuery();
  const savePreferences = useSavePreferencesMutation();

  const {
    control,
    reset,
    setValue,
    handleSubmit,
    formState: { errors }
  } = useForm<PreferencesFormValues>({
    resolver: zodResolver(preferencesFormSchema),
    defaultValues: {
      preferred_categories: [],
      preferred_subcategories: [],
      budget_mode: "moderate",
      preferred_distance_km: 8,
      home_lat: 1.3521,
      home_lng: 103.8198,
      home_address: "Singapore",
      active_days: "both",
      preferred_times: ["evening"],
      anti_preferences: []
    }
  });

  const homeLat = useWatch({
    control,
    name: "home_lat"
  });
  const homeLng = useWatch({
    control,
    name: "home_lng"
  });
  const homeAddress = useWatch({
    control,
    name: "home_address"
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
        <SingaporeLocationPickerField
          label="Home location"
          value={{
            lat: homeLat,
            lng: homeLng,
            address: homeAddress
          }}
          onChange={(next) => {
            setValue("home_lat", next.lat, { shouldDirty: true, shouldValidate: true });
            setValue("home_lng", next.lng, { shouldDirty: true, shouldValidate: true });
            setValue("home_address", next.address, { shouldDirty: true, shouldValidate: true });
          }}
          hint="This location is tied to your account and used as the default feed location."
          error={errors.home_lat?.message || errors.home_lng?.message || errors.home_address?.message}
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
    ...textStyles.subtitle
  },
  primaryBtn: {
    ...buttonStyles.primaryBtn
  },
  primaryLabel: {
    ...buttonStyles.primaryLabel
  }
});
