import { useState } from "react";
import { Pressable, StyleSheet, Text, TextInput, View } from "react-native";

import { buttonStyles, palette, textStyles, typography } from "./theme";

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
          placeholderTextColor={palette.textTertiary}
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
    gap: 8
  },
  label: {
    ...textStyles.label
  },
  row: {
    flexDirection: "row",
    gap: 10
  },
  input: {
    flex: 1,
    minHeight: 46,
    borderRadius: 14,
    borderWidth: 1,
    borderColor: palette.border,
    paddingHorizontal: 14,
    color: palette.textPrimary,
    backgroundColor: palette.surface,
    fontFamily: typography.body
  },
  inputError: {
    borderColor: palette.danger
  },
  addBtn: {
    ...buttonStyles.primaryBtn,
    paddingHorizontal: 16,
    minWidth: 68
  },
  addLabel: {
    ...buttonStyles.primaryLabel
  },
  suggestions: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 10
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
  tags: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 10
  },
  tag: {
    minHeight: 36,
    borderRadius: 999,
    backgroundColor: palette.surfaceMuted,
    borderWidth: 1,
    borderColor: palette.border,
    paddingHorizontal: 12,
    flexDirection: "row",
    alignItems: "center",
    gap: 6
  },
  tagLabel: {
    color: palette.textPrimary,
    fontFamily: typography.body,
    fontWeight: "700"
  },
  remove: {
    color: palette.textSecondary,
    fontSize: 18,
    lineHeight: 18
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
