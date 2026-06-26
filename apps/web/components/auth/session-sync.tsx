"use client";

import { useEffect } from "react";
import { useAuth, useUser } from "@clerk/nextjs";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { syncSession } from "../../lib/auth-api";

export function SessionSync() {
  const { getToken, isLoaded, isSignedIn } = useAuth();
  const { user } = useUser();
  const queryClient = useQueryClient();
  const mutation = useMutation({
    mutationFn: async () => {
      const token = await getToken();
      if (!token) {
        throw new Error("Missing Clerk session token");
      }
      return syncSession(token, {
        email: user?.primaryEmailAddress?.emailAddress ?? null,
        first_name: user?.firstName ?? null,
        last_name: user?.lastName ?? null,
        display_name: user?.fullName ?? null,
        phone_number: user?.primaryPhoneNumber?.phoneNumber ?? null
      });
    },
    onSuccess: (data) => {
      queryClient.setQueryData(["me"], data);
    }
  });

  useEffect(() => {
    if (isLoaded && isSignedIn && user && !mutation.isPending && !mutation.isSuccess) {
      mutation.mutate();
    }
  }, [isLoaded, isSignedIn, mutation, user]);

  return null;
}
