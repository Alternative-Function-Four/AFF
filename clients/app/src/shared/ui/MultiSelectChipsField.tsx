import { Pressable, StyleSheet, Text, View } from "react-native";

import type { FieldOption } from "./fieldTypes";
import { palette, textStyles, typography } from "./theme";

interface MultiSelectChipsFieldProps<T extends string> {
  label: string;
  options: FieldOption<T>[];
  values: T[];
  onChange: (nextValues: T[]) => void;
  hint?: string;
  error?: string;
}

export function MultiSelectChipsField<T extends string>({
  label,
  options,
  values,
  onChange,
  hint,
  error
}: MultiSelectChipsFieldProps<T>): JSX.Element {
  return (
    <View style={styles.wrap}>
      <Text style={styles.label}>{label}</Text>
      <View style={styles.row}>
        {options.map((option) => {
          const selected = values.includes(option.value);
          return (
            <Pressable
              key={option.value}
              accessibilityRole="button"
              accessibilityState={{ selected }}
              style={[styles.chip, selected ? styles.chipSelected : undefined]}
              onPress={() => {
                if (selected) {
                  onChange(values.filter((item) => item !== option.value));
                  return;
                }
                onChange([...values, option.value]);
              }}
            >
              <Text style={[styles.chipLabel, selected ? styles.chipLabelSelected : undefined]}>{option.label}</Text>
            </Pressable>
          );
        })}
      </View>
      {error ? <Text style={styles.error}>{error}</Text> : hint ? <Text style={styles.hint}>{hint}</Text> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: {
    gap: 8
  },
  label: {
    ...textStyles.label
  },
  row: {
    flexDirection: "row",
    gap: 10,
    flexWrap: "wrap"
  },
  chip: {
    minHeight: 42,
    borderRadius: 999,
    borderWidth: 1,
    borderColor: palette.border,
    backgroundColor: palette.surface,
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: 14
  },
  chipSelected: {
    borderColor: palette.accentSoftBorder,
    backgroundColor: palette.accentSoft
  },
  chipLabel: {
    color: palette.textPrimary,
    fontFamily: typography.body,
    fontWeight: "700"
  },
  chipLabelSelected: {
    color: palette.textPrimary
  },
  hint: {
    ...textStyles.helper
  },
  error: {
    color: palette.danger,
    fontFamily: typography.body,
    fontSize: 12
  }
});
