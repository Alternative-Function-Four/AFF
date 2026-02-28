import { Link, useRouter } from "expo-router";
import { useMemo, useState } from "react";
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from "react-native";

import { useAdminSourcesQuery, useCreateSourceMutation } from "../../src/features/admin/api";
import { APIClientError } from "../../src/shared/api/client";
import type { SourceAccessMethod, SourceStatus } from "../../src/shared/api/types";
import { FormField } from "../../src/shared/ui/FormField";
import { Screen } from "../../src/shared/ui/Screen";
import { SectionCard } from "../../src/shared/ui/SectionCard";
import { StatusMessage } from "../../src/shared/ui/StatusMessage";

type SourceStatusFilter = SourceStatus | "all";

function isStatusFilter(value: string): value is SourceStatusFilter {
  return value === "all" || value === "pending" || value === "approved" || value === "rejected" || value === "paused";
}

function isAccessMethod(value: string): value is SourceAccessMethod {
  return value === "api" || value === "rss" || value === "ics" || value === "html_extract" || value === "manual";
}

export default function AdminSourcesScreen(): JSX.Element {
  const router = useRouter();

  const [statusFilterText, setStatusFilterText] = useState<string>("all");
  const [name, setName] = useState("Example Source");
  const [url, setUrl] = useState("https://example.com/events");
  const [sourceType, setSourceType] = useState("ticketing_platform");
  const [accessMethodText, setAccessMethodText] = useState<string>("rss");
  const [termsUrl, setTermsUrl] = useState("https://example.com/terms");

  const statusFilter = useMemo(
    () => (isStatusFilter(statusFilterText) ? statusFilterText : "all"),
    [statusFilterText]
  );

  const sourcesQuery = useAdminSourcesQuery(statusFilter);
  const createSource = useCreateSourceMutation();

  const queryError =
    sourcesQuery.error instanceof APIClientError
      ? `${sourcesQuery.error.message} (${sourcesQuery.error.code})`
      : sourcesQuery.error
        ? "Unable to load sources."
        : null;

  const createError =
    createSource.error instanceof APIClientError
      ? `${createSource.error.message} (${createSource.error.code})`
      : createSource.error
        ? "Unable to create source."
        : null;

  return (
    <Screen>
      <SectionCard title="Source List">
        <FormField
          label="Status filter"
          hint="all | pending | approved | rejected | paused"
          value={statusFilterText}
          onChangeText={setStatusFilterText}
          autoCapitalize="none"
        />

        <View style={styles.row}>
          <Pressable style={styles.secondaryBtn} onPress={() => sourcesQuery.refetch()}>
            <Text style={styles.secondaryLabel}>Refresh</Text>
          </Pressable>
          <Pressable style={styles.secondaryBtn} onPress={() => router.push("/admin/ingestion")}>
            <Text style={styles.secondaryLabel}>Go to Ingestion</Text>
          </Pressable>
        </View>

        {sourcesQuery.isLoading ? <ActivityIndicator /> : null}

        {!sourcesQuery.isLoading && sourcesQuery.data?.items.length === 0 ? (
          <StatusMessage tone="info" message="No sources found for this filter. Create one below." />
        ) : null}

        {sourcesQuery.data?.items.map((source) => (
          <View key={source.id} style={styles.itemRow}>
            <Text style={styles.title}>{source.name}</Text>
            <Text style={styles.meta}>{source.status.toUpperCase()} · {source.access_method}</Text>
            <Text style={styles.meta}>{source.url}</Text>
            <Link href={`/admin/source/${source.id}`} style={styles.link}>Open source detail</Link>
          </View>
        ))}
      </SectionCard>

      <SectionCard title="Create Source">
        <FormField label="Name" value={name} onChangeText={setName} />
        <FormField label="URL" value={url} onChangeText={setUrl} autoCapitalize="none" autoCorrect={false} />
        <FormField label="Source type" value={sourceType} onChangeText={setSourceType} autoCapitalize="none" />
        <FormField
          label="Access method"
          hint="api | rss | ics | html_extract | manual"
          value={accessMethodText}
          onChangeText={setAccessMethodText}
          autoCapitalize="none"
        />
        <FormField label="Terms URL" value={termsUrl} onChangeText={setTermsUrl} autoCapitalize="none" autoCorrect={false} />

        <Pressable
          style={styles.primaryBtn}
          disabled={createSource.isPending}
          onPress={() =>
            createSource.mutate({
              name: name.trim(),
              url: url.trim(),
              source_type: sourceType.trim(),
              access_method: isAccessMethod(accessMethodText) ? accessMethodText : "rss",
              terms_url: termsUrl.trim() || undefined
            })
          }
        >
          {createSource.isPending ? <ActivityIndicator color="#FFFFFF" /> : <Text style={styles.primaryLabel}>Create Source</Text>}
        </Pressable>
      </SectionCard>

      {queryError ? <StatusMessage tone="error" message={queryError} /> : null}
      {createError ? <StatusMessage tone="error" message={createError} /> : null}
      {createSource.isSuccess ? <StatusMessage tone="success" message="Source created with pending status." /> : null}
    </Screen>
  );
}

const styles = StyleSheet.create({
  row: {
    flexDirection: "row",
    gap: 10
  },
  primaryBtn: {
    minHeight: 44,
    borderRadius: 8,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#1E4FDB"
  },
  primaryLabel: {
    color: "#FFFFFF",
    fontWeight: "700"
  },
  secondaryBtn: {
    minHeight: 44,
    flex: 1,
    borderRadius: 8,
    alignItems: "center",
    justifyContent: "center",
    borderWidth: 1,
    borderColor: "#B9C6D3",
    backgroundColor: "#FFFFFF"
  },
  secondaryLabel: {
    color: "#223B53",
    fontWeight: "600"
  },
  itemRow: {
    borderTopWidth: 1,
    borderTopColor: "#E3E8EF",
    paddingTop: 10,
    gap: 4
  },
  title: {
    fontWeight: "700",
    color: "#162B40"
  },
  meta: {
    color: "#3D5064"
  },
  link: {
    color: "#1E4FDB",
    fontWeight: "600"
  }
});
