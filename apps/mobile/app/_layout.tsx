import { ClerkProvider } from "@clerk/clerk-expo";
import { tokenCache } from "@clerk/clerk-expo/token-cache";
import { router, Stack } from "expo-router";
import { Text } from "react-native";
import { MobileAuthProvider } from "../components/auth/mobile-auth-provider";
import { OnboardingScreen } from "./onboarding/ui";

export default function RootLayout() {
  const publishableKey = process.env.EXPO_PUBLIC_CLERK_PUBLISHABLE_KEY;

  if (!publishableKey) {
    return (
      <OnboardingScreen eyebrow="Configuration" title="Clerk key missing">
        <Text style={{ color: "#64748b", fontSize: 15, lineHeight: 22 }}>
          Set EXPO_PUBLIC_CLERK_PUBLISHABLE_KEY before starting the mobile app.
        </Text>
      </OnboardingScreen>
    );
  }

  const cacheProps = tokenCache ? { tokenCache } : {};

  return (
    <ClerkProvider
      publishableKey={publishableKey}
      routerPush={(to) => router.push(to as Parameters<typeof router.push>[0])}
      routerReplace={(to) => router.replace(to as Parameters<typeof router.replace>[0])}
      {...cacheProps}
    >
      <MobileAuthProvider>
        <Stack screenOptions={{ headerShown: false }} />
      </MobileAuthProvider>
    </ClerkProvider>
  );
}
