# Architecture

KrishiAI is organized around app-specific delivery surfaces and shared internal packages.

## Apps

- `apps/web`: Next.js App Router application for browser workflows.
- `apps/mobile`: Expo application for React Native mobile workflows.
- `apps/api`: FastAPI service exposing platform APIs.

## Packages

- `packages/shared-types`: Cross-platform TypeScript contracts.
- `packages/shared-utils`: Cross-platform utilities.
- `packages/ui`: Shared React UI primitives for web-facing interfaces.

## Infrastructure

- `infrastructure/docker`: Dockerfiles for app services.
- `infrastructure/database`: database initialization assets, including PostGIS extension setup.

The repository currently contains no business, authentication, or AI domain logic.
