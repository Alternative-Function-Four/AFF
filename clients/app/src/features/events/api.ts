import { useQuery } from "@tanstack/react-query";

import { api } from "../../shared/api/client";
import { queryKeys } from "../../shared/api/queryKeys";
import type { EventDetail } from "../../shared/api/types";

export function fetchEventDetail(eventId: string): Promise<EventDetail> {
  return api.get<EventDetail>(`/v1/events/${eventId}`);
}

export function useEventDetailQuery(eventId: string) {
  return useQuery({
    queryKey: queryKeys.event(eventId),
    queryFn: () => fetchEventDetail(eventId),
    staleTime: 60_000,
    enabled: eventId.length > 0
  });
}
