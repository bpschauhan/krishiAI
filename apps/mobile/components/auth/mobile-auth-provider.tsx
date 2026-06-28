import { useAuth, useUser } from "@clerk/clerk-expo";
import type { AuthUser } from "@krishiai/auth";
import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { getMe, syncSession, updateMe, type ProfileUpdatePayload } from "../../lib/auth-api";

type MobileAuthContextValue = {
  profile: AuthUser | null;
  isSyncing: boolean;
  error: string | null;
  refreshProfile: () => Promise<AuthUser | null>;
  updateProfile: (payload: ProfileUpdatePayload) => Promise<AuthUser>;
  clearProfile: () => void;
};

const MobileAuthContext = createContext<MobileAuthContextValue | null>(null);

export function MobileAuthProvider({ children }: { children: ReactNode }) {
  const { getToken, isLoaded, isSignedIn, sessionId } = useAuth();
  const { user } = useUser();
  const [profile, setProfile] = useState<AuthUser | null>(null);
  const [isSyncing, setIsSyncing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const syncedSessionId = useRef<string | null>(null);

  const getRequiredToken = useCallback(async () => {
    const token = await getToken();
    if (!token) {
      throw new Error("Missing Clerk session token");
    }
    return token;
  }, [getToken]);

  const refreshProfile = useCallback(async () => {
    if (!isSignedIn) {
      setProfile(null);
      return null;
    }

    const token = await getRequiredToken();
    const nextProfile = await getMe(token);
    setProfile(nextProfile);
    setError(null);
    return nextProfile;
  }, [getRequiredToken, isSignedIn]);

  const updateProfile = useCallback(
    async (payload: ProfileUpdatePayload) => {
      const token = await getRequiredToken();
      const nextProfile = await updateMe(token, payload);
      setProfile(nextProfile);
      setError(null);
      return nextProfile;
    },
    [getRequiredToken]
  );

  const clearProfile = useCallback(() => {
    syncedSessionId.current = null;
    setProfile(null);
    setError(null);
  }, []);

  useEffect(() => {
    if (!isLoaded) {
      return;
    }
    if (!isSignedIn) {
      clearProfile();
      return;
    }
    if (!sessionId || syncedSessionId.current === sessionId || !user) {
      return;
    }

    let cancelled = false;
    setIsSyncing(true);
    setError(null);

    void getRequiredToken()
      .then((token) =>
        syncSession(token, {
          email: user.primaryEmailAddress?.emailAddress ?? null,
          first_name: user.firstName ?? null,
          last_name: user.lastName ?? null,
          display_name: user.fullName ?? null,
          phone_number: user.primaryPhoneNumber?.phoneNumber ?? null
        })
      )
      .then((nextProfile) => {
        if (!cancelled) {
          syncedSessionId.current = sessionId;
          setProfile(nextProfile);
        }
      })
      .catch((syncError: unknown) => {
        if (!cancelled) {
          setError(syncError instanceof Error ? syncError.message : "Unable to sync session");
        }
      })
      .finally(() => {
        if (!cancelled) {
          setIsSyncing(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [clearProfile, getRequiredToken, isLoaded, isSignedIn, sessionId, user]);

  const value = useMemo(
    () => ({
      profile,
      isSyncing,
      error,
      refreshProfile,
      updateProfile,
      clearProfile
    }),
    [clearProfile, error, isSyncing, profile, refreshProfile, updateProfile]
  );

  return <MobileAuthContext.Provider value={value}>{children}</MobileAuthContext.Provider>;
}

export function useMobileAuth() {
  const context = useContext(MobileAuthContext);
  if (!context) {
    throw new Error("useMobileAuth must be used inside MobileAuthProvider");
  }
  return context;
}
