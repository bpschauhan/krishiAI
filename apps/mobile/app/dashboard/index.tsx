import { useClerk } from "@clerk/clerk-expo";
import { getDisplayName } from "@krishiai/auth";
import { router } from "expo-router";
import { ProtectedScreen } from "../../components/auth/protected-screen";
import { useMobileAuth } from "../../components/auth/mobile-auth-provider";
import { ActionButton, ButtonRow, Metric, OnboardingScreen } from "../onboarding/ui";

export default function DashboardScreen() {
  const { signOut } = useClerk();
  const { clearProfile, profile } = useMobileAuth();

  async function logout() {
    await signOut();
    clearProfile();
    router.replace("/login");
  }

  return (
    <ProtectedScreen requiredPermissions={["dashboard:read"]}>
      <OnboardingScreen eyebrow="Dashboard" title="Farmer overview">
        <Metric label="Farmer Name" value={getDisplayName(profile)} />
        <Metric label="District" value={profile?.profile?.district ?? "Not set"} />
        <Metric label="Farm Count" value="0" />
        <Metric label="Plot Count" value="0" />
        <ActionButton label="Start onboarding" onPress={() => router.push("/onboarding/language")} />
        <ButtonRow>
          <ActionButton label="Profile" variant="secondary" onPress={() => router.push("/profile")} />
          <ActionButton label="Logout" variant="secondary" onPress={() => void logout()} />
        </ButtonRow>
      </OnboardingScreen>
    </ProtectedScreen>
  );
}
