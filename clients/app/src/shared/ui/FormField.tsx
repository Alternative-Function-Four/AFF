import { StyleSheet, Text, TextInput, TextInputProps, View } from "react-native";

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
        placeholderTextColor="#607184"
      />
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
  input: {
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
  hint: {
    color: "#607184",
    fontSize: 12
  },
  error: {
    color: "#D92D20",
    fontSize: 12
  }
});
