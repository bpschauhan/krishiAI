import { useAuth } from "@clerk/clerk-expo";
import { useRouteGuard } from "@krishiai/auth";
import { router } from "expo-router";
import { useEffect, type ReactNode } from "react";
import { ActivityIndicator, Text, View } from "react-native";
import { ActionButton, OnboardingScreen, styles } from "../../app/onboarding/ui";
import { useMobileAuth } from "./mobile-auth-provider";

type ProtectedScreenProps = {
  children: ReactNode;
  requiredPermissions?: string[];
  requiredRoles?: string[];
};

export function ProtectedScreen({
  children,
  requiredPermissions,
  requiredRoles
}: ProtectedScreenProps) {
  const { isLoaded, isSignedIn } = useAuth();
  const { error, isSyncing, profile, refreshProfile } = useMobileAuth();
  const requirements = {
    ...(requiredPermissions ? { permissions: requiredPermissions } : {}),
    ...(requiredRoles ? { roles: requiredRoles } : {})
  };
  const guard = useRouteGuard(
    {
      isLoaded: isLoaded && !isSyncing,
      isSignedIn: Boolean(isSignedIn),
      user: profile
    },
    requirements
  );

  useEffect(() => {
    if (guard.isLoading) {
      return;
    }
    if (!guard.isAuthenticated) {
      router.replace("/login");
      return;
    }
    if (!guard.isAuthorized) {
      router.replace("/unauthorized");
    }
  }, [guard.isAuthenticated, guard.isAuthorized, guard.isLoading]);

  if (guard.isLoading) {
    return <LoadingScreen message="Loading secure session..." />;
  }

  if (error) {
    return (
      <OnboardingScreen eyebrow="Session" title="Sync failed">
        <Text style={styles.error}>{error}</Text>
        <ActionButton label="Retry" onPress={() => void refreshProfile()} />
      </OnboardingScreen>
    );
  }

  if (!guard.isAuthenticated || !guard.isAuthorized) {
    return <LoadingScreen message="Checking access..." />;
  }

  return <>{children}</>;
}

export function LoadingScreen({ message }: { message: string }) {
  return (
    <OnboardingScreen eyebrow="KrishiAI" title="Loading">
      <View style={{ alignItems: "center", gap: 12 }}>
        <ActivityIndicator color="#15803d" />
        <Text style={{ color: "#64748b", fontSize: 15 }}>{message}</Text>
      </View>
    </OnboardingScreen>
  );
}
