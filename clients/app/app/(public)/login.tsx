import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation } from "@tanstack/react-query";
import { useRouter } from "expo-router";
import { useState } from "react";
import { Controller, useForm } from "react-hook-form";
import { z } from "zod";
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from "react-native";

import { demoLogin } from "../../src/features/auth/api";
import { fetchPreferences } from "../../src/features/preferences/api";
import { APIClientError } from "../../src/shared/api/client";
import { env } from "../../src/shared/config/env";
import { mapAuthSession, useSessionStore } from "../../src/shared/state/session";
import { trackEvent } from "../../src/shared/telemetry/events";
import { FormField } from "../../src/shared/ui/FormField";
import { Screen } from "../../src/shared/ui/Screen";
import { SectionCard } from "../../src/shared/ui/SectionCard";
import { StatusMessage } from "../../src/shared/ui/StatusMessage";

const loginSchema = z.object({
  display_name: z.string().trim().min(1, "Display name is required.")
});

type LoginForm = z.infer<typeof loginSchema>;

export default function LoginScreen(): JSX.Element {
  const router = useRouter();
  const setSession = useSessionStore((state) => state.setSession);
  const [showDebugOptions, setShowDebugOptions] = useState(false);
  const [useAdminSeed, setUseAdminSeed] = useState(false);

  const {
    control,
    handleSubmit,
    formState: { errors }
  } = useForm<LoginForm>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      display_name: ""
    }
  });

  const loginMutation = useMutation({
    mutationFn: ({ payload, fallbackRole }: { payload: LoginForm; fallbackRole: "member" | "admin" }) =>
      demoLogin({
        display_name: payload.display_name,
        persona_seed: fallbackRole === "admin" ? "admin" : undefined
      }).then((session) => ({ session, fallbackRole })),
    onSuccess: async ({ session, fallbackRole }) => {
      await setSession(mapAuthSession(session, fallbackRole));
      trackEvent("auth_demo_login_succeeded", {
        user_id_hash: session.user.id
      });

      try {
        const preferences = await fetchPreferences();
        if (preferences.preferred_categories.length === 0) {
          router.replace("/(user)/onboarding");
          return;
        }
        router.replace("/(user)/feed");
      } catch {
        router.replace("/(user)/feed");
      }
    }
  });

  const onSubmit = handleSubmit((values) => {
    const fallbackRole = useAdminSeed ? "admin" : "member";
    trackEvent("auth_demo_login_started", {
      surface: "mobile"
    });
    loginMutation.mutate({
      payload: values,
      fallbackRole
    });
  });

  const errorMessage =
    loginMutation.error instanceof APIClientError
      ? `${loginMutation.error.message} (${loginMutation.error.code})`
      : loginMutation.error
        ? "Unable to sign in."
        : null;

  return (
    <Screen>
      <SectionCard title="Welcome to AFF">
        <Text style={styles.subtitle}>Start in seconds and get a personalized activity feed for Singapore.</Text>
        <Controller
          control={control}
          name="display_name"
          render={({ field: { onChange, onBlur, value } }) => (
            <FormField
              label="Display name"
              value={value}
              onChangeText={onChange}
              onBlur={onBlur}
              autoCapitalize="words"
              autoCorrect={false}
              error={errors.display_name?.message}
            />
          )}
        />

        {env.enableAdmin ? (
          <View style={styles.debugSection}>
            <Pressable
              accessibilityRole="button"
              style={styles.debugToggle}
              onPress={() => {
                const nextValue = !showDebugOptions;
                setShowDebugOptions(nextValue);
                trackEvent("ui_advanced_mode_toggled", {
                  surface: "mobile",
                  enabled: nextValue
                });
              }}
            >
              <Text style={styles.debugToggleLabel}>{showDebugOptions ? "Hide debug options" : "Show debug options"}</Text>
            </Pressable>

            {showDebugOptions ? (
              <Pressable
                accessibilityRole="button"
                style={[styles.adminSeedBtn, useAdminSeed ? styles.adminSeedBtnSelected : undefined]}
                onPress={() => setUseAdminSeed((previous) => !previous)}
              >
                <Text style={[styles.adminSeedLabel, useAdminSeed ? styles.adminSeedLabelSelected : undefined]}>
                  {useAdminSeed ? "Admin debug mode enabled" : "Enable admin debug mode"}
                </Text>
              </Pressable>
            ) : null}
          </View>
        ) : null}

        <Pressable accessibilityRole="button" style={styles.primaryBtn} onPress={onSubmit} disabled={loginMutation.isPending}>
          {loginMutation.isPending ? <ActivityIndicator color="#FFFFFF" /> : <Text style={styles.primaryLabel}>Continue</Text>}
        </Pressable>
      </SectionCard>

      {errorMessage ? <StatusMessage tone="error" message={errorMessage} /> : null}
    </Screen>
  );
}

const styles = StyleSheet.create({
  subtitle: {
    color: "#445466",
    lineHeight: 20
  },
  debugSection: {
    gap: 8
  },
  debugToggle: {
    minHeight: 44,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#CCD5E0",
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#FFFFFF"
  },
  debugToggleLabel: {
    color: "#223B53",
    fontWeight: "600"
  },
  adminSeedBtn: {
    minHeight: 44,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#D7E2F7",
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#F4F7FF"
  },
  adminSeedBtnSelected: {
    borderColor: "#1E4FDB",
    backgroundColor: "#EEF3FF"
  },
  adminSeedLabel: {
    color: "#223B53",
    fontWeight: "600"
  },
  adminSeedLabelSelected: {
    color: "#11388E"
  },
  primaryBtn: {
    minHeight: 44,
    borderRadius: 8,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#1E4FDB"
  },
  primaryLabel: {
    color: "#FFFFFF",
    fontWeight: "700"
  }
});
