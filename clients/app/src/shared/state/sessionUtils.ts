import type { AuthSessionResponse, UserRole } from "../api/types";

export interface SessionUser {
  id: string;
  displayName: string;
  role: UserRole;
}

export interface StoredSession {
  accessToken: string;
  expiresAt: string;
  user: SessionUser;
}

export function mapAuthSession(
  response: AuthSessionResponse,
  fallbackRole: UserRole = "member"
): StoredSession {
  const role = response.user.role === "admin" ? "admin" : fallbackRole;
  return {
    accessToken: response.access_token,
    expiresAt: response.expires_at,
    user: {
      id: response.user.id,
      displayName: response.user.display_name,
      role
    }
  };
}

export function isSessionExpired(session: StoredSession | null, nowMs = Date.now()): boolean {
  if (!session) {
    return true;
  }
  return new Date(session.expiresAt).getTime() <= nowMs;
}
