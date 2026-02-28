import { useLocalSearchParams, useRouter } from "expo-router";
import { useMemo, useState } from "react";
import { ActivityIndicator, Pressable, StyleSheet, Text } from "react-native";

import { useAdminSourcesQuery, useApproveSourceMutation } from "../../../src/features/admin/api";
import { APIClientError } from "../../../src/shared/api/client";
import { sourceDecisionOptions } from "../../../src/shared/config/options";
import type { SourceApprovalDecision } from "../../../src/shared/api/types";
import { FormField } from "../../../src/shared/ui/FormField";
import { NumberStepperField } from "../../../src/shared/ui/NumberStepperField";
import { Screen } from "../../../src/shared/ui/Screen";
import { SectionCard } from "../../../src/shared/ui/SectionCard";
import { SegmentedControlField } from "../../../src/shared/ui/SegmentedControlField";
import { StatusMessage } from "../../../src/shared/ui/StatusMessage";

export default function AdminSourceDetailScreen(): JSX.Element {
  const router = useRouter();
  const params = useLocalSearchParams<{ sourceId?: string }>();
  const sourceId = params.sourceId ?? "";

  const sourcesQuery = useAdminSourcesQuery("all");
  const approveMutation = useApproveSourceMutation();

  const [decision, setDecision] = useState<SourceApprovalDecision>("approved");
  const [policyRisk, setPolicyRisk] = useState(20);
  const [qualityScore, setQualityScore] = useState(80);
  const [notes, setNotes] = useState("Looks compliant for prototype use.");

  const source = useMemo(
    () => sourcesQuery.data?.items.find((candidate) => candidate.id === sourceId),
    [sourceId, sourcesQuery.data?.items]
  );

  const mutationError =
    approveMutation.error instanceof APIClientError
      ? `${approveMutation.error.message} (${approveMutation.error.code})`
      : approveMutation.error
        ? "Unable to submit decision."
        : null;

  return (
    <Screen>
      <SectionCard title="Source Decision">
        {sourcesQuery.isLoading ? <ActivityIndicator /> : null}

        {source ? (
          <>
            <Text style={styles.meta}>Name: {source.name}</Text>
            <Text style={styles.meta}>Current status: {source.status}</Text>
            <Text style={styles.meta}>URL: {source.url}</Text>
          </>
        ) : (
          <StatusMessage tone="error" message="We couldn't find this source." />
        )}

        <SegmentedControlField label="Decision" options={sourceDecisionOptions} value={decision} onChange={setDecision} />

        <NumberStepperField
          label="Policy risk score"
          value={policyRisk}
          onChange={setPolicyRisk}
          min={0}
          max={100}
          step={5}
          hint="0 is safest, 100 is highest risk."
        />
        <NumberStepperField
          label="Quality score"
          value={qualityScore}
          onChange={setQualityScore}
          min={0}
          max={100}
          step={5}
          hint="Higher score means better source quality."
        />
        <FormField label="Notes" value={notes} onChangeText={setNotes} multiline numberOfLines={3} />

        <Pressable
          style={styles.primaryBtn}
          disabled={approveMutation.isPending || !source}
          onPress={() => {
            if (!source) {
              return;
            }
            approveMutation.mutate({
              sourceId,
              payload: {
                decision,
                policy_risk_score: policyRisk,
                quality_score: qualityScore,
                notes: notes.trim()
              }
            });
          }}
        >
          {approveMutation.isPending ? <ActivityIndicator color="#FFFFFF" /> : <Text style={styles.primaryLabel}>Submit Decision</Text>}
        </Pressable>

        <Pressable style={styles.secondaryBtn} onPress={() => router.push("/admin/sources")}>
          <Text style={styles.secondaryLabel}>Back to Sources</Text>
        </Pressable>
      </SectionCard>

      {mutationError ? <StatusMessage tone="error" message={mutationError} /> : null}
      {approveMutation.isSuccess ? <StatusMessage tone="success" message="Source decision updated." /> : null}
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
  },
  secondaryBtn: {
    minHeight: 44,
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
  }
});
