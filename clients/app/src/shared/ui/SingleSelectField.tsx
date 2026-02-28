import { Pressable, StyleSheet, Text, View } from "react-native";

import type { FieldOption } from "./fieldTypes";
import { palette, textStyles, typography } from "./theme";

interface SingleSelectFieldProps<T extends string> {
  label: string;
  options: FieldOption<T>[];
  value: T;
  onChange: (nextValue: T) => void;
  hint?: string;
  error?: string;
}

export function SingleSelectField<T extends string>({
  label,
  options,
  value,
  onChange,
  hint,
  error
}: SingleSelectFieldProps<T>): JSX.Element {
  return (
    <View style={styles.wrap}>
      <Text style={styles.label}>{label}</Text>
      <View style={styles.options}>
        {options.map((option) => {
          const selected = option.value === value;
          return (
            <Pressable
              key={option.value}
              accessibilityRole="button"
              accessibilityState={{ selected }}
              style={[styles.optionRow, selected ? styles.optionRowSelected : undefined]}
              onPress={() => onChange(option.value)}
            >
              <View style={[styles.radio, selected ? styles.radioSelected : undefined]}>
                {selected ? <View style={styles.radioDot} /> : null}
              </View>
              <View style={styles.textWrap}>
                <Text style={[styles.optionLabel, selected ? styles.optionLabelSelected : undefined]}>{option.label}</Text>
                {option.description ? <Text style={styles.optionDescription}>{option.description}</Text> : null}
              </View>
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
  radio: {
    width: 18,
    height: 18,
    borderRadius: 999,
    borderWidth: 1,
    borderColor: palette.borderStrong,
    alignItems: "center",
    justifyContent: "center"
  },
  radioSelected: {
    borderColor: palette.accentPressed
  },
  radioDot: {
    width: 10,
    height: 10,
    borderRadius: 999,
    backgroundColor: palette.accent
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
  hint: {
    ...textStyles.helper
  },
  error: {
    color: palette.danger,
    fontFamily: typography.body,
    fontSize: 12
  }
});
