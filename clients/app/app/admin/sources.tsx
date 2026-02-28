import { Link, useRouter } from "expo-router";
import { useState } from "react";
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from "react-native";

import { useAdminSourcesQuery, useCreateSourceMutation } from "../../src/features/admin/api";
import { APIClientError } from "../../src/shared/api/client";
import { sourceAccessMethodOptions, sourceStatusFilterOptions } from "../../src/shared/config/options";
import type { SourceAccessMethod, SourceStatus } from "../../src/shared/api/types";
import { FormField } from "../../src/shared/ui/FormField";
import { Screen } from "../../src/shared/ui/Screen";
import { SectionCard } from "../../src/shared/ui/SectionCard";
import { SegmentedControlField } from "../../src/shared/ui/SegmentedControlField";
import { SingleSelectField } from "../../src/shared/ui/SingleSelectField";
import { StatusMessage } from "../../src/shared/ui/StatusMessage";
import { buttonStyles, palette, textStyles, typography } from "../../src/shared/ui/theme";

type SourceStatusFilter = SourceStatus | "all";

export default function AdminSourcesScreen(): JSX.Element {
  const router = useRouter();

  const [statusFilter, setStatusFilter] = useState<SourceStatusFilter>("all");
  const [name, setName] = useState("Example Source");
  const [url, setUrl] = useState("https://example.com/events");
  const [sourceType, setSourceType] = useState("ticketing_platform");
  const [accessMethod, setAccessMethod] = useState<SourceAccessMethod>("rss");
  const [termsUrl, setTermsUrl] = useState("https://example.com/terms");

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
        <SegmentedControlField label="Status filter" options={sourceStatusFilterOptions} value={statusFilter} onChange={setStatusFilter} />

        <View style={styles.row}>
          <Pressable style={styles.secondaryBtn} onPress={() => sourcesQuery.refetch()}>
            <Text style={styles.secondaryLabel}>Refresh</Text>
          </Pressable>
          <Pressable style={styles.secondaryBtn} onPress={() => router.push("/admin/ingestion")}>
            <Text style={styles.secondaryLabel}>Ingestion</Text>
          </Pressable>
          <Pressable style={styles.secondaryBtn} onPress={() => router.push("/admin/notifications" as never)}>
            <Text style={styles.secondaryLabel}>Test Notifications</Text>
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
        <SingleSelectField label="Access method" options={sourceAccessMethodOptions} value={accessMethod} onChange={setAccessMethod} />
        <FormField label="Terms URL" value={termsUrl} onChangeText={setTermsUrl} autoCapitalize="none" autoCorrect={false} />

        <Pressable
          style={styles.primaryBtn}
          disabled={createSource.isPending}
          onPress={() =>
            createSource.mutate({
              name: name.trim(),
              url: url.trim(),
              source_type: sourceType.trim(),
              access_method: accessMethod,
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
    gap: 10,
    flexWrap: "wrap"
  },
  primaryBtn: {
    ...buttonStyles.primaryBtn
  },
  primaryLabel: {
    ...buttonStyles.primaryLabel
  },
  secondaryBtn: {
    ...buttonStyles.secondaryBtn,
    flex: 1,
    minWidth: 120
  },
  secondaryLabel: {
    ...buttonStyles.secondaryLabel
  },
  itemRow: {
    borderTopWidth: 1,
    borderTopColor: palette.border,
    paddingTop: 12,
    gap: 6
  },
  title: {
    color: palette.textPrimary,
    fontFamily: typography.body,
    fontWeight: "700"
  },
  meta: {
    ...textStyles.body
  },
  link: {
    color: palette.accent,
    fontFamily: typography.body,
    fontWeight: "700"
  }
});
