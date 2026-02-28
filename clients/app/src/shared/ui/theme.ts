import { Platform } from "react-native";

export const palette = {
  pageBackground: "#F7F7F7",
  pageGlowPrimary: "#FFE1E7",
  pageGlowSecondary: "#F2F2F2",
  surface: "#FFFFFF",
  surfaceMuted: "#F8F8F8",
  border: "#DDDDDD",
  borderStrong: "#B0B0B0",
  textPrimary: "#222222",
  textSecondary: "#505050",
  textTertiary: "#717171",
  accent: "#FF385C",
  accentPressed: "#E31C5F",
  accentSoft: "#FFE8ED",
  accentSoftBorder: "#FFB1C2",
  accentTextOn: "#FFFFFF",
  success: "#008A05",
  successSoft: "#E7F6EA",
  info: "#0065A9",
  infoSoft: "#E6F1FA",
  danger: "#C13515",
  dangerSoft: "#FCEDE8"
} as const;

export const typography = {
  display: Platform.select({
    ios: "System",
    android: "sans-serif-medium",
    default: "System"
  }),
  body: Platform.select({
    ios: "System",
    android: "sans-serif",
    default: "System"
  }),
  mono: Platform.select({
    ios: "Menlo",
    android: "monospace",
    default: "monospace"
  })
} as const;

export const textStyles = {
  sectionTitle: {
    color: palette.textPrimary,
    fontFamily: typography.display,
    fontSize: 20,
    lineHeight: 26,
    fontWeight: "700"
  },
  subtitle: {
    color: palette.textSecondary,
    fontFamily: typography.body,
    lineHeight: 21,
    fontSize: 15
  },
  body: {
    color: palette.textSecondary,
    fontFamily: typography.body,
    lineHeight: 20
  },
  label: {
    color: palette.textPrimary,
    fontFamily: typography.body,
    fontWeight: "700",
    fontSize: 13
  },
  helper: {
    color: palette.textTertiary,
    fontFamily: typography.body,
    fontSize: 12,
    lineHeight: 18
  }
} as const;

export const buttonStyles = {
  primaryBtn: {
    minHeight: 46,
    borderRadius: 12,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: palette.accent,
    borderWidth: 1,
    borderColor: palette.accentPressed,
    paddingHorizontal: 14
  },
  primaryLabel: {
    color: palette.accentTextOn,
    fontFamily: typography.body,
    fontWeight: "700",
    letterSpacing: 0.2
  },
  secondaryBtn: {
    minHeight: 46,
    borderRadius: 12,
    alignItems: "center",
    justifyContent: "center",
    borderWidth: 1,
    borderColor: palette.borderStrong,
    backgroundColor: palette.surface,
    paddingHorizontal: 14
  },
  secondaryLabel: {
    color: palette.textPrimary,
    fontFamily: typography.body,
    fontWeight: "700"
  },
  subtleChipBtn: {
    minHeight: 42,
    borderRadius: 999,
    borderWidth: 1,
    borderColor: palette.border,
    backgroundColor: palette.surface,
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: 12
  },
  subtleChipLabel: {
    color: palette.textPrimary,
    fontFamily: typography.body,
    fontWeight: "700",
    fontSize: 12
  }
} as const;
