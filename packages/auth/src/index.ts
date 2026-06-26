import { useMemo } from "react";

export type RoleSlug =
  | "farmer"
  | "agronomist"
  | "fpo_admin"
  | "government_officer"
  | "super_admin";

export type PermissionSlug =
  | "profile:read"
  | "profile:update"
  | "roles:read"
  | "permissions:read"
  | "farmers:read"
  | "farmers:write"
  | "farms:read"
  | "farms:write"
  | "plots:read"
  | "plots:write"
  | "dashboard:read"
  | "admin:access";

export interface AuthRole {
  id?: number;
  slug: string;
  name: string;
  description?: string | null;
}

export interface AuthPermission {
  id?: number;
  slug: string;
  name: string;
  description?: string | null;
}

export interface AuthProfile {
  id?: number;
  display_name?: string | null;
  phone_number?: string | null;
  preferred_language?: string | null;
  district?: string | null;
  village?: string | null;
}

export interface AuthUser {
  id: number;
  clerk_user_id: string;
  email?: string | null;
  first_name?: string | null;
  last_name?: string | null;
  is_active: boolean;
  profile?: AuthProfile | null;
  roles: AuthRole[];
  permissions: AuthPermission[];
}

export interface AuthSession {
  isLoaded: boolean;
  isSignedIn: boolean;
  user: AuthUser | null;
}

export function hasRole(user: Pick<AuthUser, "roles"> | null | undefined, role: string): boolean {
  return Boolean(user?.roles.some((item) => item.slug === role));
}

export function hasAnyRole(user: Pick<AuthUser, "roles"> | null | undefined, roles: string[]): boolean {
  return roles.some((role) => hasRole(user, role));
}

export function hasPermission(
  user: Pick<AuthUser, "permissions"> | null | undefined,
  permission: string
): boolean {
  return Boolean(user?.permissions.some((item) => item.slug === permission));
}

export function hasEveryPermission(
  user: Pick<AuthUser, "permissions"> | null | undefined,
  permissions: string[]
): boolean {
  return permissions.every((permission) => hasPermission(user, permission));
}

export function canAccessRoute(
  user: Pick<AuthUser, "permissions" | "roles"> | null | undefined,
  requirements: { roles?: string[]; permissions?: string[] }
): boolean {
  const roleAllowed = requirements.roles?.length ? hasAnyRole(user, requirements.roles) : true;
  const permissionAllowed = requirements.permissions?.length
    ? hasEveryPermission(user, requirements.permissions)
    : true;

  return roleAllowed && permissionAllowed;
}

export function getDisplayName(user: AuthUser | null | undefined): string {
  const profileName = user?.profile?.display_name?.trim();
  if (profileName) {
    return profileName;
  }

  const fullName = [user?.first_name, user?.last_name].filter(Boolean).join(" ").trim();
  return fullName || user?.email || "KrishiAI user";
}

export function useRouteGuard(
  session: AuthSession,
  requirements: { roles?: string[]; permissions?: string[] } = {}
): { isLoading: boolean; isAuthenticated: boolean; isAuthorized: boolean } {
  return useMemo(
    () => ({
      isLoading: !session.isLoaded,
      isAuthenticated: session.isLoaded && session.isSignedIn,
      isAuthorized:
        session.isLoaded && session.isSignedIn
          ? canAccessRoute(session.user, requirements)
          : false
    }),
    [requirements, session.isLoaded, session.isSignedIn, session.user]
  );
}
