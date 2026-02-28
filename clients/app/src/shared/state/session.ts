import { create } from "zustand";

import { readStoredSession, writeStoredSession } from "./sessionStorage";
import { isSessionExpired, type StoredSession } from "./sessionUtils";

interface SessionState {
  hydrated: boolean;
  session: StoredSession | null;
  hydrateFromStorage: () => Promise<void>;
  setSession: (session: StoredSession) => Promise<void>;
  clearSession: () => Promise<void>;
}

export { mapAuthSession, isSessionExpired } from "./sessionUtils";

export const useSessionStore = create<SessionState>((set) => ({
  hydrated: false,
  session: null,
  async hydrateFromStorage() {
    try {
      const stored = await readStoredSession();
      set({ hydrated: true, session: stored });
    } catch {
      set({ hydrated: true, session: null });
    }
  },
  async setSession(session: StoredSession) {
    set({ session });
    try {
      await writeStoredSession(session);
    } catch {
      // Keep in-memory session even when persistence fails.
    }
  },
  async clearSession() {
    set({ session: null });
    try {
      await writeStoredSession(null);
    } catch {
      // Ignore persistence cleanup failures.
    }
  }
}));

export function getActiveAccessToken(): string | null {
  const { session } = useSessionStore.getState();
  if (!session || isSessionExpired(session)) {
    return null;
  }
  return session.accessToken;
}
