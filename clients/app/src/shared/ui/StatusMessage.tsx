import { StyleSheet, Text, View } from "react-native";

import { palette, typography } from "./theme";

interface StatusMessageProps {
  tone?: "error" | "info" | "success";
  message: string;
}

export function StatusMessage({ tone = "info", message }: StatusMessageProps): JSX.Element {
  return (
    <View style={[styles.container, tone === "error" ? styles.error : tone === "success" ? styles.success : styles.info]}>
      <Text style={styles.text}>{message}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    borderRadius: 14,
    paddingHorizontal: 14,
    paddingVertical: 12,
    borderWidth: 1
  },
  info: {
    backgroundColor: palette.infoSoft,
    borderColor: "#BFD5EA"
  },
  error: {
    backgroundColor: palette.dangerSoft,
    borderColor: "#F0C3BE"
  },
  success: {
    backgroundColor: palette.successSoft,
    borderColor: "#C8E1D1"
  },
  text: {
    color: palette.textPrimary,
    fontFamily: typography.body,
    lineHeight: 20
  }
});
