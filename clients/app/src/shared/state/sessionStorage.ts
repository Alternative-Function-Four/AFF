import { Platform } from "react-native";
import * as SecureStore from "expo-secure-store";

import type { StoredSession } from "./sessionUtils";

const STORAGE_KEY = "aff.session.v1";

function readWebStorage(): Storage | null {
  if (typeof window === "undefined") {
    return null;
  }
  try {
    return window.sessionStorage;
  } catch {
    return null;
  }
}

export async function readStoredSession(): Promise<StoredSession | null> {
  if (Platform.OS === "web") {
    const storage = readWebStorage();
    const raw = storage?.getItem(STORAGE_KEY);
    if (!raw) {
      return null;
    }
    try {
      return JSON.parse(raw) as StoredSession;
    } catch {
      return null;
    }
  }

  const raw = await SecureStore.getItemAsync(STORAGE_KEY);
  if (!raw) {
    return null;
  }
  try {
    return JSON.parse(raw) as StoredSession;
  } catch {
    return null;
  }
}

export async function writeStoredSession(session: StoredSession | null): Promise<void> {
  if (Platform.OS === "web") {
    const storage = readWebStorage();
    if (!storage) {
      return;
    }
    if (session == null) {
      storage.removeItem(STORAGE_KEY);
      return;
    }
    storage.setItem(STORAGE_KEY, JSON.stringify(session));
    return;
  }

  if (session == null) {
    await SecureStore.deleteItemAsync(STORAGE_KEY);
    return;
  }
  await SecureStore.setItemAsync(STORAGE_KEY, JSON.stringify(session));
}
