import type { AuthUser, AuthRole, AuthPermission } from "@krishiai/auth";

export const apiBaseUrl =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type ProfileUpdatePayload = {
  first_name?: string | null;
  last_name?: string | null;
  display_name?: string | null;
  phone_number?: string | null;
  preferred_language?: string | null;
  district?: string | null;
  village?: string | null;
};

export type SyncPayload = {
  email?: string | null;
  first_name?: string | null;
  last_name?: string | null;
  display_name?: string | null;
  phone_number?: string | null;
};

export async function apiRequest<T>(
  path: string,
  token: string,
  init: RequestInit = {}
): Promise<T> {
  const response = await fetch(`${apiBaseUrl}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
      ...init.headers
    }
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed with status ${response.status}`);
  }

  return (await response.json()) as T;
}

export function syncSession(token: string, payload: SyncPayload): Promise<AuthUser> {
  return apiRequest<AuthUser>("/api/v1/auth/sync", token, {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function getMe(token: string): Promise<AuthUser> {
  return apiRequest<AuthUser>("/api/v1/me", token);
}

export function updateMe(token: string, payload: ProfileUpdatePayload): Promise<AuthUser> {
  return apiRequest<AuthUser>("/api/v1/me", token, {
    method: "PATCH",
    body: JSON.stringify(payload)
  });
}

export function getRoles(token: string): Promise<AuthRole[]> {
  return apiRequest<AuthRole[]>("/api/v1/roles", token);
}

export function getPermissions(token: string): Promise<AuthPermission[]> {
  return apiRequest<AuthPermission[]>("/api/v1/permissions", token);
}
