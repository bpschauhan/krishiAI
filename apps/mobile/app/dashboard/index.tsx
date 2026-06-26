import { ActionButton, Metric, OnboardingScreen } from "../onboarding/ui";
import { router } from "expo-router";

export default function DashboardScreen() {
  return (
    <OnboardingScreen eyebrow="Dashboard" title="Farmer overview">
      <Metric label="Farmer Name" value="Ramesh Kumar" />
      <Metric label="District" value="Lucknow" />
      <Metric label="Farm Count" value="1" />
      <Metric label="Plot Count" value="1" />
      <ActionButton label="Start new onboarding" onPress={() => router.push("/onboarding/language")} />
    </OnboardingScreen>
  );
}
