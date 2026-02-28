import { Stack } from "expo-router";
import { StatusBar } from "expo-status-bar";

import { AppProviders } from "../src/shared/providers/AppProviders";
import { palette, typography } from "../src/shared/ui/theme";

export default function RootLayout(): JSX.Element {
  return (
    <AppProviders>
      <StatusBar style="dark" />
      <Stack
        screenOptions={{
          headerTitleStyle: {
            fontWeight: "700",
            fontFamily: typography.display
          },
          headerStyle: {
            backgroundColor: palette.surface
          },
          headerTintColor: palette.textPrimary,
          headerShadowVisible: false,
          contentStyle: {
            backgroundColor: palette.pageBackground
          }
        }}
      >
        <Stack.Screen name="index" options={{ headerShown: false }} />
        <Stack.Screen name="(public)/login" options={{ title: "AFF Login" }} />
        <Stack.Screen name="(user)/feed" options={{ title: "Feed" }} />
        <Stack.Screen name="(user)/onboarding" options={{ title: "Onboarding" }} />
        <Stack.Screen name="(user)/preferences" options={{ title: "Preferences" }} />
        <Stack.Screen name="(user)/notifications" options={{ title: "Notifications" }} />
        <Stack.Screen name="(user)/event/[eventId]" options={{ title: "Event Detail" }} />
        <Stack.Screen name="admin/sources" options={{ title: "Admin Sources" }} />
        <Stack.Screen name="admin/source/[sourceId]" options={{ title: "Source Decision" }} />
        <Stack.Screen name="admin/ingestion" options={{ title: "Admin Ingestion" }} />
        <Stack.Screen name="admin/notifications" options={{ title: "Admin Notifications" }} />
      </Stack>
    </AppProviders>
  );
}
