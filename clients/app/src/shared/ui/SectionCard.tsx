import { PropsWithChildren } from "react";
import { StyleSheet, Text, View } from "react-native";

interface SectionCardProps extends PropsWithChildren {
  title?: string;
}

export function SectionCard({ title, children }: SectionCardProps): JSX.Element {
  return (
    <View style={styles.card}>
      {title ? <Text style={styles.title}>{title}</Text> : null}
      <View style={styles.content}>{children}</View>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: "#FFFFFF",
    borderRadius: 12,
    padding: 14,
    gap: 10,
    shadowColor: "#000",
    shadowOpacity: 0.05,
    shadowOffset: { width: 0, height: 2 },
    shadowRadius: 6,
    elevation: 1
  },
  title: {
    fontSize: 17,
    fontWeight: "700",
    color: "#12263A"
  },
  content: {
    gap: 10
  }
});
