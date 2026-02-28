import { PropsWithChildren } from "react";
import { KeyboardAvoidingView, Platform, ScrollView, StyleSheet, View } from "react-native";

import { palette } from "./theme";

interface ScreenProps extends PropsWithChildren {
  scroll?: boolean;
}

export function Screen({ children, scroll = true }: ScreenProps): JSX.Element {
  if (!scroll) {
    return (
      <View style={styles.container}>
        <View style={styles.content}>{children}</View>
      </View>
    );
  }

  return (
    <KeyboardAvoidingView behavior={Platform.OS === "ios" ? "padding" : undefined} style={styles.container}>
      <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
        <View style={styles.content}>{children}</View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: palette.pageBackground
  },
  scrollContent: {
    paddingHorizontal: 16,
    paddingTop: 14,
    paddingBottom: 22
  },
  content: {
    width: "100%",
    maxWidth: 980,
    alignSelf: "center",
    gap: 16
  }
});
