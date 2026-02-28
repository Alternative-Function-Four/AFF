import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation } from "@tanstack/react-query";
import { useRouter } from "expo-router";
import { Controller, useForm } from "react-hook-form";
import { z } from "zod";
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from "react-native";

import { demoLogin } from "../../src/features/auth/api";
import { fetchPreferences } from "../../src/features/preferences/api";
import { APIClientError } from "../../src/shared/api/client";
import { mapAuthSession, useSessionStore } from "../../src/shared/state/session";
import { trackEvent } from "../../src/shared/telemetry/events";
import { FormField } from "../../src/shared/ui/FormField";
import { Screen } from "../../src/shared/ui/Screen";
import { SectionCard } from "../../src/shared/ui/SectionCard";
import { StatusMessage } from "../../src/shared/ui/StatusMessage";

const loginSchema = z.object({
  display_name: z.string().trim().min(1, "Display name is required."),
  persona_seed: z.string().trim().optional()
});

type LoginForm = z.infer<typeof loginSchema>;

export default function LoginScreen(): JSX.Element {
  const router = useRouter();
  const setSession = useSessionStore((state) => state.setSession);

  const {
    control,
    handleSubmit,
    setValue,
    formState: { errors }
  } = useForm<LoginForm>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      display_name: "",
      persona_seed: ""
    }
  });

  const loginMutation = useMutation({
    mutationFn: ({ payload, fallbackRole }: { payload: LoginForm; fallbackRole: "member" | "admin" }) =>
      demoLogin({
        display_name: payload.display_name,
        persona_seed: payload.persona_seed?.length ? payload.persona_seed : undefined
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
    trackEvent("auth_demo_login_started", {
      surface: "mobile"
    });

    loginMutation.mutate({
      payload: values,
      fallbackRole: values.persona_seed?.trim().toLowerCase() === "admin" ? "admin" : "member"
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
        <Text style={styles.subtitle}>Use demo login to start onboarding and get a personalized Singapore feed.</Text>
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
        <Controller
          control={control}
          name="persona_seed"
          render={({ field: { onChange, onBlur, value } }) => (
            <FormField
              label="Persona seed (optional)"
              hint={'Use "admin" to open admin routes in debug mode.'}
              value={value}
              onChangeText={onChange}
              onBlur={onBlur}
              autoCapitalize="none"
              autoCorrect={false}
            />
          )}
        />

        <View style={styles.row}>
          <Pressable accessibilityRole="button" style={styles.secondaryBtn} onPress={() => setValue("persona_seed", "admin")}>
            <Text style={styles.secondaryLabel}>Use Admin Seed</Text>
          </Pressable>
          <Pressable accessibilityRole="button" style={styles.primaryBtn} onPress={onSubmit} disabled={loginMutation.isPending}>
            {loginMutation.isPending ? (
              <ActivityIndicator color="#FFFFFF" />
            ) : (
              <Text style={styles.primaryLabel}>Continue</Text>
            )}
          </Pressable>
        </View>
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
  row: {
    flexDirection: "row",
    gap: 10
  },
  primaryBtn: {
    minHeight: 44,
    flex: 1,
    borderRadius: 8,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#1E4FDB"
  },
  primaryLabel: {
    color: "#FFFFFF",
    fontWeight: "700"
  },
  secondaryBtn: {
    minHeight: 44,
    flex: 1,
    borderRadius: 8,
    alignItems: "center",
    justifyContent: "center",
    borderWidth: 1,
    borderColor: "#B9C6D3",
    backgroundColor: "#FFFFFF"
  },
  secondaryLabel: {
    color: "#223B53",
    fontWeight: "600"
  }
});
