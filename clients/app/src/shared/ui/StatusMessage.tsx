import { StyleSheet, Text, View } from "react-native";

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
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 10
  },
  info: {
    backgroundColor: "#E9F2FF"
  },
  error: {
    backgroundColor: "#FFE8E8"
  },
  success: {
    backgroundColor: "#E9FBEF"
  },
  text: {
    color: "#12263A"
  }
});
