import { StyleSheet, Text, TextInput, TextInputProps, View } from "react-native";

import { palette, textStyles, typography } from "./theme";

interface FormFieldProps extends TextInputProps {
  label: string;
  hint?: string;
  error?: string;
}

export function FormField({ label, hint, error, style, ...inputProps }: FormFieldProps): JSX.Element {
  return (
    <View style={styles.wrap}>
      <Text style={styles.label}>{label}</Text>
      <TextInput
        {...inputProps}
        style={[styles.input, style, error ? styles.inputError : undefined]}
        placeholderTextColor={palette.textTertiary}
      />
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
  input: {
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
  hint: {
    ...textStyles.helper
  },
  error: {
    color: palette.danger,
    fontFamily: typography.body,
    fontSize: 12,
    lineHeight: 18
  }
});
