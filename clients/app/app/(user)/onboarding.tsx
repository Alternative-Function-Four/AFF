import { zodResolver } from "@hookform/resolvers/zod";
import { useRouter } from "expo-router";
import { Controller, useForm, useWatch } from "react-hook-form";
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
import { useSavePreferencesMutation } from "../../src/features/preferences/api";
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

const defaultValues = toPreferenceFormDefaults({
  preferred_categories: ["events", "food", "nightlife"],
  preferred_subcategories: ["indie_music"],
  budget_mode: "moderate",
  preferred_distance_km: 8,
  home_lat: 1.3521,
  home_lng: 103.8198,
  home_address: "Singapore",
  active_days: "both",
  preferred_times: ["evening"],
  anti_preferences: ["large_crowds"]
});

export default function OnboardingScreen(): JSX.Element {
  const router = useRouter();
  const savePreferences = useSavePreferencesMutation();

  const {
    control,
    setValue,
    handleSubmit,
    formState: { errors }
  } = useForm<PreferencesFormValues>({
    resolver: zodResolver(preferencesFormSchema),
    defaultValues
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
        ? "We couldn't save your preferences. Please try again."
        : null;

  return (
    <Screen>
      <SectionCard title="Tell AFF what you enjoy">
        <Text style={styles.subtitle}>Pick what sounds good and we'll personalize your feed right away.</Text>

        <Controller
          control={control}
          name="preferred_categories"
          render={({ field: { value, onChange } }) => (
            <TagInputField
              label="Favorite categories"
              values={value}
              onChange={onChange}
              suggestions={suggestedCategoryTags}
              hint="Select a few or add your own."
              error={errors.preferred_categories?.message}
            />
          )}
        />
        <Controller
          control={control}
          name="preferred_subcategories"
          render={({ field: { value, onChange } }) => (
            <TagInputField
              label="Specific interests"
              values={value}
              onChange={onChange}
              suggestions={suggestedSubcategoryTags}
              hint="Optional, but helpful for better matches."
            />
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
              label="How far are you willing to travel? (km)"
              keyboardType="numeric"
              value={String(value)}
              onChangeText={onChange}
              onBlur={onBlur}
              hint="Most users pick between 3 and 12 km."
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
          hint="Set your home area to make your feed location-aware from day one."
          error={errors.home_lat?.message || errors.home_lng?.message || errors.home_address?.message}
        />
        <Controller
          control={control}
          name="active_days"
          render={({ field: { value, onChange } }) => (
            <SegmentedControlField label="When do you usually go out?" options={activeDaysOptions} value={value} onChange={onChange} />
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
              label="What should we avoid?"
              values={value}
              onChange={onChange}
              suggestions={suggestedAntiPreferenceTags}
              hint="Optional. Remove any item by tapping it."
            />
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
    ...textStyles.subtitle
  },
  primaryBtn: {
    ...buttonStyles.primaryBtn
  },
  primaryLabel: {
    ...buttonStyles.primaryLabel
  }
});
