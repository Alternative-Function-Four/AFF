import { Pressable, StyleSheet, Text, View } from "react-native";

import type { EntityOption } from "./fieldTypes";

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
  checkbox: {
    width: 20,
    height: 20,
    borderRadius: 4,
    borderWidth: 1,
    borderColor: "#7C8D9F",
    alignItems: "center",
    justifyContent: "center"
  },
  checkboxSelected: {
    borderColor: "#1E4FDB",
    backgroundColor: "#1E4FDB"
  },
  check: {
    color: "#FFFFFF",
    fontWeight: "800",
    fontSize: 12
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
  empty: {
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
