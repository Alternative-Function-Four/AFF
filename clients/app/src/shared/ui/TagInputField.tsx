import { useState } from "react";
import { Pressable, StyleSheet, Text, TextInput, View } from "react-native";

interface TagInputFieldProps {
  label: string;
  values: string[];
  onChange: (nextValues: string[]) => void;
  suggestions?: string[];
  placeholder?: string;
  hint?: string;
  error?: string;
}

function normalizeTag(value: string): string {
  return value.trim().replace(/\s+/g, "_").toLowerCase();
}

export function TagInputField({
  label,
  values,
  onChange,
  suggestions = [],
  placeholder = "Add a custom item",
  hint,
  error
}: TagInputFieldProps): JSX.Element {
  const [draft, setDraft] = useState("");

  const addTag = (raw: string) => {
    const normalized = normalizeTag(raw);
    if (!normalized.length) {
      return;
    }

    if (values.includes(normalized)) {
      setDraft("");
      return;
    }

    onChange([...values, normalized]);
    setDraft("");
  };

  return (
    <View style={styles.wrap}>
      <Text style={styles.label}>{label}</Text>

      <View style={styles.row}>
        <TextInput
          value={draft}
          onChangeText={setDraft}
          style={[styles.input, error ? styles.inputError : undefined]}
          placeholder={placeholder}
          placeholderTextColor="#607184"
          autoCapitalize="none"
          autoCorrect={false}
          onSubmitEditing={() => addTag(draft)}
        />
        <Pressable style={styles.addBtn} accessibilityRole="button" onPress={() => addTag(draft)}>
          <Text style={styles.addLabel}>Add</Text>
        </Pressable>
      </View>

      {suggestions.length > 0 ? (
        <View style={styles.suggestions}>
          {suggestions.map((suggestion) => {
            const normalized = normalizeTag(suggestion);
            const selected = values.includes(normalized);
            return (
              <Pressable
                key={suggestion}
                accessibilityRole="button"
                accessibilityState={{ selected }}
                style={[styles.chip, selected ? styles.chipSelected : undefined]}
                onPress={() => (selected ? onChange(values.filter((value) => value !== normalized)) : onChange([...values, normalized]))}
              >
                <Text style={[styles.chipLabel, selected ? styles.chipLabelSelected : undefined]}>{suggestion}</Text>
              </Pressable>
            );
          })}
        </View>
      ) : null}

      <View style={styles.tags}>
        {values.map((tag) => (
          <Pressable
            key={tag}
            accessibilityRole="button"
            style={styles.tag}
            onPress={() => onChange(values.filter((value) => value !== tag))}
          >
            <Text style={styles.tagLabel}>{tag}</Text>
            <Text style={styles.remove}>×</Text>
          </Pressable>
        ))}
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
    gap: 8
  },
  input: {
    flex: 1,
    minHeight: 44,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#CCD5E0",
    paddingHorizontal: 12,
    color: "#12263A",
    backgroundColor: "#FFFFFF"
  },
  inputError: {
    borderColor: "#D92D20"
  },
  addBtn: {
    minHeight: 44,
    borderRadius: 8,
    paddingHorizontal: 16,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#1E4FDB"
  },
  addLabel: {
    color: "#FFFFFF",
    fontWeight: "700"
  },
  suggestions: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8
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
  tags: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8
  },
  tag: {
    minHeight: 36,
    borderRadius: 999,
    backgroundColor: "#EEF3FF",
    borderWidth: 1,
    borderColor: "#C5D3FA",
    paddingHorizontal: 10,
    flexDirection: "row",
    alignItems: "center",
    gap: 6
  },
  tagLabel: {
    color: "#1A3149",
    fontWeight: "600"
  },
  remove: {
    color: "#375CAE",
    fontSize: 18,
    lineHeight: 18
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
