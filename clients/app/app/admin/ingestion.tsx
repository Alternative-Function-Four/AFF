import { useMemo, useState } from "react";
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from "react-native";

import { useAdminSourcesQuery, useRunIngestionMutation } from "../../src/features/admin/api";
import { APIClientError } from "../../src/shared/api/client";
import { ingestionReasonOptions } from "../../src/shared/config/options";
import { trackEvent } from "../../src/shared/telemetry/events";
import { EntityMultiSelectField } from "../../src/shared/ui/EntityMultiSelectField";
import { Screen } from "../../src/shared/ui/Screen";
import { SectionCard } from "../../src/shared/ui/SectionCard";
import { SingleSelectField } from "../../src/shared/ui/SingleSelectField";
import { StatusMessage } from "../../src/shared/ui/StatusMessage";
import { setAllSelections } from "../../src/shared/ui/selection";

type IngestionReason = "scheduled_sync" | "manual_retry" | "policy_recheck";

export default function AdminIngestionScreen(): JSX.Element {
  const approvedSourcesQuery = useAdminSourcesQuery("approved");
  const runIngestion = useRunIngestionMutation();

  const [selectedSourceIds, setSelectedSourceIds] = useState<string[]>([]);
  const [reason, setReason] = useState<IngestionReason>("scheduled_sync");

  const options = useMemo(
    () =>
      approvedSourcesQuery.data?.items.map((source) => ({
        id: source.id,
        label: source.name,
        description: `${source.source_type} · ${source.url}`
      })) ?? [],
    [approvedSourcesQuery.data?.items]
  );

  const allIds = useMemo(() => options.map((option) => option.id), [options]);
  const allSelected = allIds.length > 0 && selectedSourceIds.length === allIds.length;

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

        <View style={styles.row}>
          <Pressable
            accessibilityRole="button"
            style={styles.secondaryBtn}
            onPress={() => {
              const nextValues = setAllSelections(allIds, !allSelected);
              setSelectedSourceIds(nextValues);
              trackEvent("admin_ingestion_selection_updated", {
                surface: "admin_web",
                selected_count: nextValues.length
              });
            }}
            disabled={allIds.length === 0}
          >
            <Text style={styles.secondaryLabel}>{allSelected ? "Clear Selection" : "Select All Approved"}</Text>
          </Pressable>
          <Pressable style={styles.secondaryBtn} onPress={() => approvedSourcesQuery.refetch()}>
            <Text style={styles.secondaryLabel}>Refresh</Text>
          </Pressable>
        </View>

        <Text style={styles.meta}>Selected sources: {selectedSourceIds.length}</Text>

        <EntityMultiSelectField
          label="Approved sources"
          options={options}
          values={selectedSourceIds}
          onChange={(nextValues) => {
            setSelectedSourceIds(nextValues);
            trackEvent("admin_ingestion_selection_updated", {
              surface: "admin_web",
              selected_count: nextValues.length
            });
          }}
          emptyMessage="No approved sources yet."
        />

        <SingleSelectField
          label="Reason"
          options={ingestionReasonOptions}
          value={reason}
          onChange={setReason}
        />

        <Pressable
          style={styles.primaryBtn}
          disabled={runIngestion.isPending || selectedSourceIds.length === 0}
          onPress={() =>
            runIngestion.mutate({
              source_ids: selectedSourceIds,
              reason
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
  row: {
    flexDirection: "row",
    gap: 10,
    flexWrap: "wrap"
  },
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
  },
  secondaryBtn: {
    minHeight: 44,
    flex: 1,
    borderRadius: 8,
    alignItems: "center",
    justifyContent: "center",
    borderWidth: 1,
    borderColor: "#B9C6D3",
    backgroundColor: "#FFFFFF",
    paddingHorizontal: 12
  },
  secondaryLabel: {
    color: "#223B53",
    fontWeight: "600"
  }
});
