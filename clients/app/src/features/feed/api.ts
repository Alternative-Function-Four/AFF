import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "../../shared/api/client";
import { queryKeys } from "../../shared/api/queryKeys";
import type {
  BudgetMode,
  CreatedResponse,
  EventFeedbackRequest,
  FeedMode,
  FeedResponse,
  TimeWindow
} from "../../shared/api/types";
import { trackEvent } from "../../shared/telemetry/events";

export interface FeedParams {
  lat: number;
  lng: number;
  time_window: TimeWindow;
  budget: BudgetMode;
  mode: FeedMode;
}

export function fetchFeed(params: FeedParams): Promise<FeedResponse> {
  trackEvent("feed_request_started", {
    surface: "mobile"
  });

  return api.get<FeedResponse>("/v1/feed", { query: { ...params } }).then((response) => {
    trackEvent("feed_request_succeeded", {
      request_id: response.request_id,
      surface: "mobile"
    });
    return response;
  });
}

export function submitFeedback(eventId: string, payload: EventFeedbackRequest): Promise<CreatedResponse> {
  trackEvent("feed_feedback_submitted", {
    surface: "mobile"
  });

  return api.post<CreatedResponse>(`/v1/events/${eventId}/feedback`, payload).then((response) => {
    trackEvent("feed_feedback_succeeded", {
      surface: "mobile"
    });
    return response;
  });
}

export function useFeedQuery(params: FeedParams) {
  return useQuery({
    queryKey: queryKeys.feed(params),
    queryFn: () => fetchFeed(params),
    staleTime: 30_000
  });
}

export function useFeedbackMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ eventId, payload }: { eventId: string; payload: EventFeedbackRequest }) =>
      submitFeedback(eventId, payload),
    onSuccess: async (_data, variables) => {
      await queryClient.invalidateQueries({ queryKey: ["feed"] });
      await queryClient.invalidateQueries({ queryKey: queryKeys.event(variables.eventId) });
    }
  });
}
