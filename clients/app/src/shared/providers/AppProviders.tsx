import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { PropsWithChildren, useEffect, useState } from "react";
import { ActivityIndicator, StyleSheet, View } from "react-native";

import { useSessionStore } from "../state/session";

export function AppProviders({ children }: PropsWithChildren): JSX.Element {
  const [queryClient] = useState(() =>
    new QueryClient({
      defaultOptions: {
        queries: {
          retry: 1,
          staleTime: 30_000
        }
      }
    })
  );

  const hydrateFromStorage = useSessionStore((state) => state.hydrateFromStorage);
  const hydrated = useSessionStore((state) => state.hydrated);

  useEffect(() => {
    void hydrateFromStorage();
  }, [hydrateFromStorage]);

  if (!hydrated) {
    return (
      <View style={styles.loadingWrap}>
        <ActivityIndicator size="large" />
      </View>
    );
  }

  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
}

const styles = StyleSheet.create({
  loadingWrap: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#F5F7FA"
  }
});
