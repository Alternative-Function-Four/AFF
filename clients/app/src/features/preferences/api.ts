import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "../../shared/api/client";
import { queryKeys } from "../../shared/api/queryKeys";
import type { PreferenceProfile, PreferenceProfileInput } from "../../shared/api/types";

export function fetchPreferences(): Promise<PreferenceProfile> {
  return api.get<PreferenceProfile>("/v1/preferences");
}

export function savePreferences(payload: PreferenceProfileInput): Promise<PreferenceProfile> {
  return api.put<PreferenceProfile>("/v1/preferences", payload);
}

export function usePreferencesQuery() {
  return useQuery({
    queryKey: queryKeys.preferences,
    queryFn: fetchPreferences,
    staleTime: 5 * 60_000
  });
}

export function useSavePreferencesMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: savePreferences,
    onMutate: async (next) => {
      await queryClient.cancelQueries({ queryKey: queryKeys.preferences });
      const previous = queryClient.getQueryData<PreferenceProfile>(queryKeys.preferences);

      if (previous) {
        queryClient.setQueryData<PreferenceProfile>(queryKeys.preferences, {
          ...previous,
          ...next,
          updated_at: new Date().toISOString()
        });
      }

      return { previous };
    },
    onError: (_error, _payload, context) => {
      if (context?.previous) {
        queryClient.setQueryData(queryKeys.preferences, context.previous);
      }
    },
    onSettled: async () => {
      await queryClient.invalidateQueries({ queryKey: queryKeys.preferences });
      await queryClient.invalidateQueries({ queryKey: ["feed"] });
    }
  });
}
