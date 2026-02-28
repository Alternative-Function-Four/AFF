export type AppEnvironment = "local" | "preview" | "demo";

function requiredApiBaseUrl(): string {
  const value = process.env.EXPO_PUBLIC_API_BASE_URL;
  if (!value || value.trim().length === 0) {
    throw new Error("Missing required env var: EXPO_PUBLIC_API_BASE_URL");
  }
  return value;
}

function parseNumber(value: string | undefined, fallback: number): number {
  if (!value) {
    return fallback;
  }
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
}

function parseBoolean(value: string | undefined, fallback: boolean): boolean {
  if (value === "true") {
    return true;
  }
  if (value === "false") {
    return false;
  }
  return fallback;
}

function parseAppEnvironment(value: string | undefined): AppEnvironment {
  if (value === "preview" || value === "demo" || value === "local") {
    return value;
  }
  return "local";
}

const apiBaseUrl = requiredApiBaseUrl().replace(/\/$/, "");
const appEnv = parseAppEnvironment(process.env.EXPO_PUBLIC_APP_ENV);

export const env = {
  apiBaseUrl,
  appEnv,
  enableAdmin: parseBoolean(process.env.EXPO_PUBLIC_ENABLE_ADMIN, false),
  defaultLat: parseNumber(process.env.EXPO_PUBLIC_DEFAULT_LAT, 1.29027),
  defaultLng: parseNumber(process.env.EXPO_PUBLIC_DEFAULT_LNG, 103.851959)
};
