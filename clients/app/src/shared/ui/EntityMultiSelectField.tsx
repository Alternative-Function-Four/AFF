import { Pressable, StyleSheet, Text, View } from "react-native";

import type { EntityOption } from "./fieldTypes";
import { palette, textStyles, typography } from "./theme";

interface EntityMultiSelectFieldProps {
  label: string;
  options: EntityOption[];
  values: string[];
  onChange: (nextValues: string[]) => void;
  emptyMessage?: string;
  hint?: string;
  error?: string;
}

export function EntityMultiSelectField({
  label,
  options,
  values,
  onChange,
  emptyMessage = "No options are available yet.",
  hint,
  error
}: EntityMultiSelectFieldProps): JSX.Element {
  return (
    <View style={styles.wrap}>
      <Text style={styles.label}>{label}</Text>
      {options.length === 0 ? (
        <Text style={styles.empty}>{emptyMessage}</Text>
      ) : (
        <View style={styles.options}>
          {options.map((option) => {
            const selected = values.includes(option.id);
            return (
              <Pressable
                key={option.id}
                accessibilityRole="button"
                accessibilityState={{ selected }}
                style={[styles.optionRow, selected ? styles.optionRowSelected : undefined]}
                onPress={() => {
                  if (selected) {
                    onChange(values.filter((item) => item !== option.id));
                    return;
                  }
                  onChange([...values, option.id]);
                }}
              >
                <View style={[styles.checkbox, selected ? styles.checkboxSelected : undefined]}>
                  {selected ? <Text style={styles.check}>✓</Text> : null}
                </View>
                <View style={styles.textWrap}>
                  <Text style={[styles.optionLabel, selected ? styles.optionLabelSelected : undefined]}>{option.label}</Text>
                  {option.description ? <Text style={styles.optionDescription}>{option.description}</Text> : null}
                </View>
              </Pressable>
            );
          })}
        </View>
      )}
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
  options: {
    gap: 10
  },
  optionRow: {
    minHeight: 46,
    borderRadius: 14,
    borderWidth: 1,
    borderColor: palette.border,
    backgroundColor: palette.surface,
    paddingHorizontal: 14,
    paddingVertical: 12,
    flexDirection: "row",
    gap: 12,
    alignItems: "center"
  },
  optionRowSelected: {
    borderColor: palette.accentSoftBorder,
    backgroundColor: palette.accentSoft
  },
  checkbox: {
    width: 20,
    height: 20,
    borderRadius: 6,
    borderWidth: 1,
    borderColor: palette.borderStrong,
    alignItems: "center",
    justifyContent: "center"
  },
  checkboxSelected: {
    borderColor: palette.accentPressed,
    backgroundColor: palette.accent
  },
  check: {
    color: palette.accentTextOn,
    fontWeight: "800",
    fontSize: 12
  },
  textWrap: {
    flex: 1,
    gap: 4
  },
  optionLabel: {
    color: palette.textPrimary,
    fontFamily: typography.body,
    fontWeight: "700"
  },
  optionLabelSelected: {
    color: palette.textPrimary
  },
  optionDescription: {
    ...textStyles.helper
  },
  empty: {
    ...textStyles.helper
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
