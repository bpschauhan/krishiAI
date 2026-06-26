import { router } from "expo-router";
import { ActionButton, OnboardingScreen } from "./onboarding/ui";

export default function IndexScreen() {
  return (
    <OnboardingScreen eyebrow="KrishiAI Mobile" title="Farmer setup">
      <ActionButton label="Start onboarding" onPress={() => router.push("/onboarding/language")} />
      <ActionButton label="Open dashboard" variant="secondary" onPress={() => router.push("/dashboard")} />
    </OnboardingScreen>
  );
}
