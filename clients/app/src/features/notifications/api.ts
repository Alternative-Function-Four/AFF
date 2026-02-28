import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "../../shared/api/client";
import { queryKeys } from "../../shared/api/queryKeys";
import { trackEvent } from "../../shared/telemetry/events";
import type {
  NotificationListResponse,
  TestNotificationRequest,
  TestNotificationResponse
} from "../../shared/api/types";

export function fetchNotifications(limit = 20): Promise<NotificationListResponse> {
  return api.get<NotificationListResponse>("/v1/notifications", {
    query: { limit }
  });
}

export function triggerTestNotification(payload: TestNotificationRequest): Promise<TestNotificationResponse> {
  trackEvent("notification_test_triggered", {
    surface: "mobile"
  });
  return api.post<TestNotificationResponse>("/v1/notifications/test", payload);
}

export function useNotificationsQuery(limit = 20) {
  return useQuery({
    queryKey: queryKeys.notifications(limit),
    queryFn: () => fetchNotifications(limit),
    staleTime: 30_000
  });
}

export function useTestNotificationMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: triggerTestNotification,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["notifications"] });
    }
  });
}
