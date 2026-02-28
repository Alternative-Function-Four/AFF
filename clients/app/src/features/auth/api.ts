import { api } from "../../shared/api/client";
import type { AuthSessionResponse, DemoLoginRequest, PasswordLoginRequest } from "../../shared/api/types";

export function demoLogin(payload: DemoLoginRequest): Promise<AuthSessionResponse> {
  return api.post<AuthSessionResponse>("/v1/auth/demo-login", payload, { auth: false });
}

export function passwordLogin(payload: PasswordLoginRequest): Promise<AuthSessionResponse> {
  return api.post<AuthSessionResponse>("/v1/auth/login", payload, { auth: false });
}
