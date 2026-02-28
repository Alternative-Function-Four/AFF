import { Pressable, StyleSheet, Text, View } from "react-native";

import type { FieldOption } from "./fieldTypes";

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
    gap: 6
  },
  label: {
    color: "#12263A",
    fontWeight: "600"
  },
  options: {
    gap: 8
  },
  optionRow: {
    minHeight: 44,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: "#CCD5E0",
    backgroundColor: "#FFFFFF",
    paddingHorizontal: 12,
    paddingVertical: 10,
    flexDirection: "row",
    gap: 10,
    alignItems: "center"
  },
  optionRowSelected: {
    borderColor: "#1E4FDB",
    backgroundColor: "#EEF3FF"
  },
  radio: {
    width: 18,
    height: 18,
    borderRadius: 999,
    borderWidth: 1,
    borderColor: "#7C8D9F",
    alignItems: "center",
    justifyContent: "center"
  },
  radioSelected: {
    borderColor: "#1E4FDB"
  },
  radioDot: {
    width: 10,
    height: 10,
    borderRadius: 999,
    backgroundColor: "#1E4FDB"
  },
  textWrap: {
    flex: 1,
    gap: 2
  },
  optionLabel: {
    color: "#1A3149",
    fontWeight: "600"
  },
  optionLabelSelected: {
    color: "#11388E"
  },
  optionDescription: {
    color: "#607184",
    fontSize: 12
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
