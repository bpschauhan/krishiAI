import { useAuth } from "@clerk/clerk-expo";
import { router } from "expo-router";
import { useEffect } from "react";
import { ActionButton, OnboardingScreen } from "./onboarding/ui";

export default function IndexScreen() {
  const { isLoaded, isSignedIn } = useAuth();

  useEffect(() => {
    if (isLoaded && isSignedIn) {
      router.replace("/dashboard");
    }
  }, [isLoaded, isSignedIn]);

  return (
    <OnboardingScreen eyebrow="KrishiAI Mobile" title="Authentication">
      <ActionButton label="Login" onPress={() => router.push("/login")} />
      <ActionButton label="Create account" variant="secondary" onPress={() => router.push("/signup")} />
    </OnboardingScreen>
  );
}
