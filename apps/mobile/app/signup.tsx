import { isClerkAPIResponseError, useAuth, useSignUp } from "@clerk/clerk-expo";
import { router } from "expo-router";
import { useEffect, useState } from "react";
import { Text } from "react-native";
import { validateEmail, validatePassword, validateRequired } from "../lib/mobile-auth-validation";
import { ActionButton, ButtonRow, Field, OnboardingScreen } from "./onboarding/ui";

export default function SignupScreen() {
  const { isSignedIn } = useAuth();
  const { isLoaded, setActive, signUp } = useSignUp();
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [verificationCode, setVerificationCode] = useState("");
  const [pendingVerification, setPendingVerification] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (isSignedIn) {
      router.replace("/dashboard");
    }
  }, [isSignedIn]);

  async function createAccount() {
    const nextErrors: Record<string, string> = {};
    const firstNameError = validateRequired(firstName, "First name");
    const emailError = validateEmail(email);
    const passwordError = validatePassword(password);
    if (firstNameError) {
      nextErrors.firstName = firstNameError;
    }
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
      const signUpPayload = {
        emailAddress: email.trim(),
        password,
        firstName: firstName.trim(),
        ...(lastName.trim() ? { lastName: lastName.trim() } : {})
      };

      await signUp.create(signUpPayload);
      await signUp.prepareEmailAddressVerification({ strategy: "email_code" });
      setPendingVerification(true);
      setErrors({});
    } catch (error: unknown) {
      setErrors({ form: getClerkErrorMessage(error) });
    } finally {
      setIsSubmitting(false);
    }
  }

  async function verifyAccount() {
    const codeError = validateRequired(verificationCode, "Verification code");
    if (codeError || !isLoaded) {
      setErrors({ verificationCode: codeError ?? "Verification is not ready." });
      return;
    }

    setIsSubmitting(true);
    try {
      const result = await signUp.attemptEmailAddressVerification({
        code: verificationCode.trim()
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
    <OnboardingScreen eyebrow="Authentication" title={pendingVerification ? "Verify email" : "Signup"}>
      {!pendingVerification ? (
        <>
          <Field error={errors.firstName} label="First name" onChangeText={setFirstName} placeholder="Ramesh" value={firstName} />
          <Field label="Last name" onChangeText={setLastName} placeholder="Kumar" value={lastName} />
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
            placeholder="At least 8 characters"
            secureTextEntry
            value={password}
          />
          {errors.form ? <Text style={{ color: "#dc2626", fontSize: 13 }}>{errors.form}</Text> : null}
          <ButtonRow>
            <ActionButton label="Login" variant="secondary" onPress={() => router.replace("/login")} />
            <ActionButton disabled={isSubmitting} label={isSubmitting ? "Creating..." : "Signup"} onPress={() => void createAccount()} />
          </ButtonRow>
        </>
      ) : (
        <>
          <Text style={{ color: "#64748b", fontSize: 15, lineHeight: 22 }}>
            Enter the verification code Clerk sent to {email.trim()}.
          </Text>
          <Field
            error={errors.verificationCode}
            keyboardType="number-pad"
            label="Verification code"
            onChangeText={setVerificationCode}
            placeholder="123456"
            value={verificationCode}
          />
          {errors.form ? <Text style={{ color: "#dc2626", fontSize: 13 }}>{errors.form}</Text> : null}
          <ButtonRow>
            <ActionButton label="Back" variant="secondary" onPress={() => setPendingVerification(false)} />
            <ActionButton disabled={isSubmitting} label={isSubmitting ? "Verifying..." : "Verify"} onPress={() => void verifyAccount()} />
          </ButtonRow>
        </>
      )}
    </OnboardingScreen>
  );
}

function getClerkErrorMessage(error: unknown): string {
  if (isClerkAPIResponseError(error)) {
    return error.errors[0]?.longMessage ?? error.errors[0]?.message ?? "Signup failed.";
  }
  return error instanceof Error ? error.message : "Signup failed.";
}
