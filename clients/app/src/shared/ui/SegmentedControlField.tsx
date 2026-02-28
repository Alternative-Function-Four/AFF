import { Pressable, StyleSheet, Text, View } from "react-native";

import type { FieldOption } from "./fieldTypes";

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
    gap: 6
  },
  label: {
    color: "#12263A",
    fontWeight: "600"
  },
  row: {
    flexDirection: "row",
    gap: 8,
    flexWrap: "wrap"
  },
  segment: {
    minHeight: 44,
    minWidth: 84,
    borderRadius: 999,
    borderWidth: 1,
    borderColor: "#CCD5E0",
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: 12,
    backgroundColor: "#FFFFFF"
  },
  segmentSelected: {
    backgroundColor: "#1E4FDB",
    borderColor: "#1E4FDB"
  },
  segmentLabel: {
    color: "#1A3149",
    fontWeight: "600"
  },
  segmentLabelSelected: {
    color: "#FFFFFF"
  },
  hint: {
    color: "#607184",
    fontSize: 12
  },
  error: {
    color: "#D92D20",
    fontSize: 12
  }
});
