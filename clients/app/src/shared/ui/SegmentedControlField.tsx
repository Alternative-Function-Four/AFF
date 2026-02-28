import { Pressable, StyleSheet, Text, View } from "react-native";

import type { FieldOption } from "./fieldTypes";
import { palette, textStyles, typography } from "./theme";

interface SegmentedControlFieldProps<T extends string> {
  label: string;
  options: FieldOption<T>[];
  value: T;
  onChange: (nextValue: T) => void;
  hint?: string;
  error?: string;
}

export function SegmentedControlField<T extends string>({
  label,
  options,
  value,
  onChange,
  hint,
  error
}: SegmentedControlFieldProps<T>): JSX.Element {
  return (
    <View style={styles.wrap}>
      <Text style={styles.label}>{label}</Text>
      <View style={styles.row}>
        {options.map((option) => {
          const selected = option.value === value;
          return (
            <Pressable
              key={option.value}
              accessibilityRole="button"
              accessibilityState={{ selected }}
              onPress={() => onChange(option.value)}
              style={[styles.segment, selected ? styles.segmentSelected : undefined]}
            >
              <Text style={[styles.segmentLabel, selected ? styles.segmentLabelSelected : undefined]}>{option.label}</Text>
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
  segment: {
    minHeight: 44,
    minWidth: 84,
    borderRadius: 999,
    borderWidth: 1,
    borderColor: palette.border,
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: 14,
    backgroundColor: palette.surface
  },
  segmentSelected: {
    backgroundColor: palette.accent,
    borderColor: palette.accentPressed
  },
  segmentLabel: {
    color: palette.textPrimary,
    fontFamily: typography.body,
    fontWeight: "700"
  },
  segmentLabelSelected: {
    color: palette.accentTextOn
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
