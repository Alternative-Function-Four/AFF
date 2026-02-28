import { env } from "../config/env";
import { getActiveAccessToken, useSessionStore } from "../state/session";
import type { ErrorEnvelope } from "./types";

export class APIClientError extends Error {
  public readonly code: string;
  public readonly status: number;
  public readonly details: Record<string, unknown>;
  public readonly requestId?: string;

  constructor(args: {
    code: string;
    message: string;
    status: number;
    details?: Record<string, unknown>;
    requestId?: string;
  }) {
    super(args.message);
    this.name = "APIClientError";
    this.code = args.code;
    this.status = args.status;
    this.details = args.details ?? {};
    this.requestId = args.requestId;
  }
}

type Primitive = string | number | boolean;

type RequestOptions = {
  method?: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
  body?: unknown;
  query?: Record<string, Primitive | null | undefined>;
  auth?: boolean;
  headers?: Record<string, string>;
};

function buildUrl(path: string, query?: RequestOptions["query"]): string {
  const url = new URL(path, `${env.apiBaseUrl}/`);
  if (query) {
    for (const [key, value] of Object.entries(query)) {
      if (value == null) {
        continue;
      }
      url.searchParams.set(key, String(value));
    }
  }
  return url.toString();
}

function asErrorEnvelope(value: unknown): ErrorEnvelope | null {
  if (typeof value !== "object" || value == null) {
    return null;
  }

  const candidate = value as Record<string, unknown>;
  if (
    typeof candidate.code === "string" &&
    typeof candidate.message === "string" &&
    typeof candidate.request_id === "string" &&
    typeof candidate.details === "object"
  ) {
    return {
      code: candidate.code,
      message: candidate.message,
      details: (candidate.details as Record<string, unknown>) ?? {},
      request_id: candidate.request_id
    };
  }

  return null;
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const method = options.method ?? "GET";
  const auth = options.auth ?? true;

  const headers: Record<string, string> = {
    Accept: "application/json",
    ...(options.headers ?? {})
  };

  if (options.body != null) {
    headers["Content-Type"] = "application/json";
  }

  if (auth) {
    const token = getActiveAccessToken();
    if (!token) {
      throw new APIClientError({
        code: "UNAUTHORIZED",
        message: "Session is missing or expired.",
        status: 401
      });
    }
    headers.Authorization = `Bearer ${token}`;
  }

  let response: Response;
  try {
    response = await fetch(buildUrl(path, options.query), {
      method,
      headers,
      body: options.body == null ? undefined : JSON.stringify(options.body)
    });
  } catch (error) {
    throw new APIClientError({
      code: "NETWORK_ERROR",
      message: error instanceof Error ? error.message : "Network request failed.",
      status: 0
    });
  }

  const text = await response.text();
  let payload: unknown = null;
  if (text) {
    try {
      payload = JSON.parse(text);
    } catch {
      payload = { raw: text };
    }
  }

  if (!response.ok) {
    const envelope = asErrorEnvelope(payload);
    if (response.status === 401) {
      void useSessionStore.getState().clearSession();
    }

    if (envelope) {
      throw new APIClientError({
        code: envelope.code,
        message: envelope.message,
        status: response.status,
        details: envelope.details,
        requestId: envelope.request_id
      });
    }

    throw new APIClientError({
      code: "HTTP_ERROR",
      message: `Request failed (${response.status}).`,
      status: response.status,
      details: { payload }
    });
  }

  return payload as T;
}

export const api = {
  get<T>(path: string, options?: Omit<RequestOptions, "method" | "body">) {
    return request<T>(path, { ...options, method: "GET" });
  },
  post<T>(path: string, body?: unknown, options?: Omit<RequestOptions, "method" | "body">) {
    return request<T>(path, { ...options, method: "POST", body });
  },
  put<T>(path: string, body?: unknown, options?: Omit<RequestOptions, "method" | "body">) {
    return request<T>(path, { ...options, method: "PUT", body });
  }
};
