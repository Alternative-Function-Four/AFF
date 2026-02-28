import { Pressable, StyleSheet, Text, View } from "react-native";

import type { FieldOption } from "./fieldTypes";

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
  chip: {
    minHeight: 44,
    borderRadius: 999,
    borderWidth: 1,
    borderColor: "#CCD5E0",
    backgroundColor: "#FFFFFF",
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: 12
  },
  chipSelected: {
    borderColor: "#1E4FDB",
    backgroundColor: "#EEF3FF"
  },
  chipLabel: {
    color: "#1A3149",
    fontWeight: "600"
  },
  chipLabelSelected: {
    color: "#11388E"
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
