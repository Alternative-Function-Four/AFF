import { beforeEach, describe, expect, it, vi } from "vitest";

let authToken: string | null = null;
const clearSessionMock = vi.fn(async () => undefined);

vi.mock("../config/env", () => ({
  env: {
    apiBaseUrl: "http://aff.local"
  }
}));

vi.mock("../state/session", () => ({
  getActiveAccessToken: () => authToken,
  useSessionStore: {
    getState: () => ({
      clearSession: clearSessionMock
    })
  }
}));

import { APIClientError, api } from "./client";

describe("api client", () => {
  beforeEach(() => {
    authToken = null;
    clearSessionMock.mockClear();
    vi.restoreAllMocks();
  });

  it("rejects authenticated calls without token", async () => {
    await expect(api.get("/v1/preferences")).rejects.toMatchObject({
      code: "UNAUTHORIZED",
      status: 401
    });
  });

  it("sends auth header and query params for success path", async () => {
    authToken = "tok_123";
    const fetchMock = vi.fn(async (..._args: unknown[]) => new Response(JSON.stringify({ ok: true }), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);

    const response = await api.get<{ ok: boolean }>("/v1/feed", {
      query: {
        lat: 1.29,
        lng: 103.85
      }
    });

    expect(response.ok).toBe(true);
    expect(fetchMock).toHaveBeenCalledTimes(1);

    const call = fetchMock.mock.calls[0];
    expect(call).toBeDefined();
    const url = String(call?.[0]);
    const init = (call?.[1] ?? {}) as RequestInit;
    expect(url).toContain("/v1/feed?");
    expect(url).toContain("lat=1.29");
    expect(url).toContain("lng=103.85");
    expect((init.headers as Record<string, string>).Authorization).toBe("Bearer tok_123");
  });

  it("maps backend error envelope", async () => {
    authToken = "tok_123";
    const fetchMock = vi.fn(async (..._args: unknown[]) =>
      new Response(
        JSON.stringify({
          code: "SOURCE_NOT_APPROVED",
          message: "Only approved sources can be ingested",
          details: { source_id: "s-1" },
          request_id: "req_123"
        }),
        { status: 403 }
      )
    );
    vi.stubGlobal("fetch", fetchMock);

    await expect(api.post("/v1/admin/ingestion/run", { source_ids: ["s-1"], reason: "manual" })).rejects.toMatchObject({
      code: "SOURCE_NOT_APPROVED",
      status: 403,
      requestId: "req_123"
    });
  });

  it("normalizes non-json server errors and clears session on 401", async () => {
    authToken = "tok_123";
    const fetchMock = vi.fn(async (..._args: unknown[]) => new Response("server exploded", { status: 401 }));
    vi.stubGlobal("fetch", fetchMock);

    try {
      await api.get("/v1/preferences");
      throw new Error("Expected API error");
    } catch (error) {
      expect(error).toBeInstanceOf(APIClientError);
      expect((error as APIClientError).code).toBe("HTTP_ERROR");
      expect((error as APIClientError).status).toBe(401);
      expect(clearSessionMock).toHaveBeenCalledTimes(1);
    }
  });
});
