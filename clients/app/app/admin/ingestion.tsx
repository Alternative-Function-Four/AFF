import { useMemo, useState } from "react";
import { ActivityIndicator, Pressable, StyleSheet, Text } from "react-native";

import { useAdminSourcesQuery, useRunIngestionMutation } from "../../src/features/admin/api";
import { APIClientError } from "../../src/shared/api/client";
import { FormField } from "../../src/shared/ui/FormField";
import { Screen } from "../../src/shared/ui/Screen";
import { SectionCard } from "../../src/shared/ui/SectionCard";
import { StatusMessage } from "../../src/shared/ui/StatusMessage";

function splitIds(value: string): string[] {
  return value
    .split(",")
    .map((item) => item.trim())
    .filter((item) => item.length > 0);
}

export default function AdminIngestionScreen(): JSX.Element {
  const approvedSourcesQuery = useAdminSourcesQuery("approved");
  const runIngestion = useRunIngestionMutation();

  const [sourceIdsText, setSourceIdsText] = useState("");
  const [reason, setReason] = useState("scheduled_sync");

  const suggestedIds = useMemo(
    () => approvedSourcesQuery.data?.items.map((source) => source.id).join(", ") ?? "",
    [approvedSourcesQuery.data?.items]
  );

  const mutationError =
    runIngestion.error instanceof APIClientError
      ? `${runIngestion.error.message} (${runIngestion.error.code})`
      : runIngestion.error
        ? "Unable to run ingestion."
        : null;

  return (
    <Screen>
      <SectionCard title="Ingestion Trigger">
        {approvedSourcesQuery.isLoading ? <ActivityIndicator /> : null}

        {!approvedSourcesQuery.isLoading && approvedSourcesQuery.data?.items.length === 0 ? (
          <StatusMessage tone="info" message="No approved sources available. Approve at least one source first." />
        ) : null}

        {approvedSourcesQuery.data?.items.map((source) => (
          <Text style={styles.meta} key={source.id}>
            {source.id} · {source.name}
          </Text>
        ))}

        <FormField
          label="Source IDs (comma-separated)"
          value={sourceIdsText}
          onChangeText={setSourceIdsText}
          autoCapitalize="none"
          autoCorrect={false}
          hint={suggestedIds.length > 0 ? `Approved: ${suggestedIds}` : "Enter at least one source id"}
        />
        <FormField label="Reason" value={reason} onChangeText={setReason} autoCapitalize="none" autoCorrect={false} />

        <Pressable
          style={styles.primaryBtn}
          disabled={runIngestion.isPending || splitIds(sourceIdsText).length === 0}
          onPress={() =>
            runIngestion.mutate({
              source_ids: splitIds(sourceIdsText),
              reason: reason.trim().length ? reason.trim() : "scheduled_sync"
            })
          }
        >
          {runIngestion.isPending ? <ActivityIndicator color="#FFFFFF" /> : <Text style={styles.primaryLabel}>Run Ingestion</Text>}
        </Pressable>

        {runIngestion.data ? (
          <StatusMessage
            tone="success"
            message={`Queued ${runIngestion.data.queued_count} source(s). Job ID: ${runIngestion.data.job_id}`}
          />
        ) : null}
      </SectionCard>

      {mutationError ? <StatusMessage tone="error" message={mutationError} /> : null}
    </Screen>
  );
}

const styles = StyleSheet.create({
  meta: {
    color: "#3D5064"
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
  }
});
