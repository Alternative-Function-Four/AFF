import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "../../shared/api/client";
import { queryKeys } from "../../shared/api/queryKeys";
import { trackEvent } from "../../shared/telemetry/events";
import type {
  IngestionRunRequest,
  IngestionRunResponse,
  Source,
  SourceApprovalRequest,
  SourceCreateRequest,
  SourceListResponse,
  SourceStatus
} from "../../shared/api/types";

export function fetchSources(status: SourceStatus | "all" = "all"): Promise<SourceListResponse> {
  return api.get<SourceListResponse>("/v1/admin/sources", {
    query: {
      status: status === "all" ? null : status
    }
  });
}

export function createSource(payload: SourceCreateRequest): Promise<Source> {
  return api.post<Source>("/v1/admin/sources", payload);
}

export function approveSource(sourceId: string, payload: SourceApprovalRequest): Promise<Source> {
  trackEvent("admin_source_approved", {
    surface: "admin_web"
  });
  return api.post<Source>(`/v1/admin/sources/${sourceId}/approve`, payload);
}

export function runIngestion(payload: IngestionRunRequest): Promise<IngestionRunResponse> {
  trackEvent("admin_ingestion_run_triggered", {
    surface: "admin_web"
  });
  return api.post<IngestionRunResponse>("/v1/admin/ingestion/run", payload);
}

export function useAdminSourcesQuery(status: SourceStatus | "all" = "all") {
  return useQuery({
    queryKey: queryKeys.adminSources(status),
    queryFn: () => fetchSources(status),
    staleTime: 20_000
  });
}

export function useCreateSourceMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createSource,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["admin", "sources"] });
    }
  });
}

export function useApproveSourceMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ sourceId, payload }: { sourceId: string; payload: SourceApprovalRequest }) =>
      approveSource(sourceId, payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["admin", "sources"] });
    }
  });
}

export function useRunIngestionMutation() {
  return useMutation({
    mutationFn: runIngestion
  });
}
