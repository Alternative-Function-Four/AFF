import { PropsWithChildren } from "react";
import { StyleSheet, Text, View } from "react-native";

import { palette, textStyles } from "./theme";

interface SectionCardProps extends PropsWithChildren {
  title?: string;
}

export function SectionCard({ title, children }: SectionCardProps): JSX.Element {
  return (
    <View style={styles.card}>
      {title ? (
        <View style={styles.header}>
          <Text style={styles.title}>{title}</Text>
          <View style={styles.rule} />
        </View>
      ) : null}
      <View style={styles.content}>{children}</View>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: palette.surface,
    borderRadius: 16,
    paddingHorizontal: 16,
    paddingVertical: 16,
    gap: 12,
    borderWidth: 1,
    borderColor: palette.border,
    shadowColor: "#000000",
    shadowOpacity: 0.06,
    shadowOffset: { width: 0, height: 2 },
    shadowRadius: 8,
    elevation: 2
  },
  header: {
    gap: 10
  },
  title: {
    ...textStyles.sectionTitle
  },
  rule: {
    width: "100%",
    borderBottomWidth: 1,
    borderBottomColor: palette.border
  },
  content: {
    gap: 10
  }
});
