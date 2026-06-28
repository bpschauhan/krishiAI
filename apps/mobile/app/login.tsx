import { isClerkAPIResponseError, useAuth, useSignIn } from "@clerk/clerk-expo";
import { router } from "expo-router";
import { useEffect, useState } from "react";
import { Text } from "react-native";
import { validateEmail, validatePassword } from "../lib/mobile-auth-validation";
import { ActionButton, ButtonRow, Field, OnboardingScreen } from "./onboarding/ui";

export default function LoginScreen() {
  const { isSignedIn } = useAuth();
  const { isLoaded, setActive, signIn } = useSignIn();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (isSignedIn) {
      router.replace("/dashboard");
    }
  }, [isSignedIn]);

  async function submit() {
    const nextErrors: Record<string, string> = {};
    const emailError = validateEmail(email);
    const passwordError = validatePassword(password);
    if (emailError) {
      nextErrors.email = emailError;
    }
    if (passwordError) {
      nextErrors.password = passwordError;
    }
    setErrors(nextErrors);
    if (Object.keys(nextErrors).length > 0 || !isLoaded) {
      return;
    }

    setIsSubmitting(true);
    try {
      const result = await signIn.create({
        identifier: email.trim(),
        password
      });

      if (result.status === "complete" && result.createdSessionId) {
        await setActive({ session: result.createdSessionId });
        router.replace("/dashboard");
        return;
      }

      setErrors({ form: "Additional verification is required for this account." });
    } catch (error: unknown) {
      setErrors({ form: getClerkErrorMessage(error) });
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <OnboardingScreen eyebrow="Authentication" title="Login">
      <Field
        autoCapitalize="none"
        error={errors.email}
        keyboardType="email-address"
        label="Email"
        onChangeText={setEmail}
        placeholder="farmer@example.com"
        value={email}
      />
      <Field
        error={errors.password}
        label="Password"
        onChangeText={setPassword}
        placeholder="Password"
        secureTextEntry
        value={password}
      />
      {errors.form ? <Text style={{ color: "#dc2626", fontSize: 13 }}>{errors.form}</Text> : null}
      <ButtonRow>
        <ActionButton label="Create account" variant="secondary" onPress={() => router.push("/signup")} />
        <ActionButton disabled={isSubmitting} label={isSubmitting ? "Logging in..." : "Login"} onPress={() => void submit()} />
      </ButtonRow>
    </OnboardingScreen>
  );
}

function getClerkErrorMessage(error: unknown): string {
  if (isClerkAPIResponseError(error)) {
    return error.errors[0]?.longMessage ?? error.errors[0]?.message ?? "Authentication failed.";
  }
  return error instanceof Error ? error.message : "Authentication failed.";
}
