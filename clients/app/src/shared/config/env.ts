export type AppEnvironment = "local" | "preview" | "demo";

function required(name: "EXPO_PUBLIC_API_BASE_URL"): string {
  const value = process.env[name];
  if (!value || value.trim().length === 0) {
    throw new Error(`Missing required env var: ${name}`);
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

const apiBaseUrl = required("EXPO_PUBLIC_API_BASE_URL").replace(/\/$/, "");
const appEnv = (process.env.EXPO_PUBLIC_APP_ENV ?? "local") as AppEnvironment;

export const env = {
  apiBaseUrl,
  appEnv,
  enableAdmin: parseBoolean(process.env.EXPO_PUBLIC_ENABLE_ADMIN, false),
  defaultLat: parseNumber(process.env.EXPO_PUBLIC_DEFAULT_LAT, 1.29027),
  defaultLng: parseNumber(process.env.EXPO_PUBLIC_DEFAULT_LNG, 103.851959)
};
