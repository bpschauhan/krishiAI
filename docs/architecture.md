# Architecture

KrishiAI is organized around app-specific delivery surfaces and shared internal packages.

## Apps

- `apps/web`: Next.js App Router application for browser workflows.
- `apps/mobile`: Expo application for React Native mobile workflows.
- `apps/api`: FastAPI service exposing platform APIs.

## Packages

- `packages/auth`: Shared auth contracts, role helpers, permission helpers, and route guard logic.
- `packages/shared-types`: Cross-platform TypeScript contracts.
- `packages/shared-utils`: Cross-platform utilities.
- `packages/ui`: Shared React UI primitives for web-facing interfaces.

## Infrastructure

- `infrastructure/docker`: Dockerfiles for app services.
- `infrastructure/database`: database initialization assets, including PostGIS extension setup.

## Authentication And Identity

Phase 2 authentication uses Clerk across web and mobile:

- Web uses `@clerk/nextjs` with App Router middleware, login/signup pages, protected dashboard/profile routes, and session synchronization to the API.
- Mobile uses `@clerk/clerk-expo`, Expo Router, and `expo-secure-store` token cache for persistent sessions.
- API requests use Clerk JWT bearer tokens. FastAPI verifies tokens with Clerk JWKS before resolving a synchronized local `User`.

The API owns the application identity and authorization model:

- `User`
- `UserProfile`
- `Role`
- `Permission`
- `UserRole`
- `PermissionRole`

Permissions are database driven. Route authorization checks required permission slugs against permissions loaded from assigned roles; authorization is not based on hardcoded role checks.

## Mobile Auth Flow

Expo starts with a root `ClerkProvider` configured with the app publishable key and SecureStore token cache. The mobile auth provider listens for authenticated Clerk sessions, requests a Clerk JWT, calls `POST /api/v1/auth/sync`, and stores the synchronized profile in local React state. Protected mobile screens use the shared `@krishiai/auth` route guard helpers and redirect unauthenticated users to `/login`.

Protected mobile routes include dashboard, profile, and onboarding screens. Profile editing calls `GET /api/v1/me` and `PATCH /api/v1/me` using the active Clerk JWT.

## Security

The API includes:

- Clerk JWT verification with issuer, JWKS URL, and optional audience validation.
- Authentication dependency for synchronized users.
- Permission dependency decorators for protected endpoints.
- Ownership helper for owner-or-permission checks.
- CSRF checks for cookie-authenticated unsafe web requests.
- Rate limiting with Redis and in-memory fallback.
- Security headers middleware.

## Migrations

Alembic is configured in `apps/api`. The Phase 2 auth migration creates identity/RBAC tables and inserts the required system role and permission catalog. It does not create sample users.
