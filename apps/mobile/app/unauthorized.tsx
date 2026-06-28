import { useClerk } from "@clerk/clerk-expo";
import { router } from "expo-router";
import { Text } from "react-native";
import { ActionButton, ButtonRow, OnboardingScreen } from "./onboarding/ui";

export default function UnauthorizedScreen() {
  const { signOut } = useClerk();

  async function logout() {
    await signOut();
    router.replace("/login");
  }

  return (
    <OnboardingScreen eyebrow="Access denied" title="Unauthorized">
      <Text style={{ color: "#64748b", fontSize: 15, lineHeight: 22 }}>
        Your account does not have permission to open this screen.
      </Text>
      <ButtonRow>
        <ActionButton label="Dashboard" variant="secondary" onPress={() => router.replace("/dashboard")} />
        <ActionButton label="Logout" onPress={() => void logout()} />
      </ButtonRow>
    </OnboardingScreen>
  );
}
