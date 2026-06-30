# KrishiAI

KrishiAI is a production-grade monorepo foundation for an AI-powered agricultural operating system focused on farmers in Uttar Pradesh, India.

The current implementation includes the Phase 1 onboarding foundation and Phase 2 authentication and identity layer.

## Stack

- Web: Next.js 15, TypeScript, Tailwind CSS, shadcn/ui conventions
- Mobile: React Native, Expo, TypeScript
- API: FastAPI, Python 3.13
- Database: PostgreSQL with PostGIS
- Cache: Redis
- Infrastructure: Docker and Docker Compose
- Monorepo: pnpm workspaces
- Auth: Clerk with FastAPI JWT verification, RBAC, and Expo SecureStore session persistence
- Geospatial: PostGIS-backed Farm Digital Twin core boundaries and regions

## Structure

```text
krishiai/
├── apps/
│   ├── api/
│   ├── mobile/
│   └── web/
├── packages/
│   ├── shared-types/
│   ├── shared-utils/
│   └── ui/
├── infrastructure/
│   ├── database/
│   └── docker/
├── docs/
├── docker-compose.yml
├── package.json
├── pnpm-workspace.yaml
└── README.md
```

## Prerequisites

- Node.js 22+
- pnpm 9+
- Docker Desktop
- Python 3.13, only needed for local API development outside Docker

## Environment

Create a local environment file when custom values are needed:

```bash
cp .env.example .env
```

Docker Compose includes safe local defaults, so the core stack can start without a committed `.env` file.

Authentication requires Clerk configuration:

```bash
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_...
EXPO_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_...
CLERK_SECRET_KEY=sk_...
CLERK_ISSUER_URL=https://your-clerk-issuer
CLERK_JWKS_URL=https://your-clerk-issuer/.well-known/jwks.json
```

`CLERK_JWT_AUDIENCE` is optional and should match the configured Clerk JWT template audience when one is used.

## Start Locally

Install JavaScript workspace dependencies:

```bash
pnpm install
```

Start the web app, API, PostgreSQL/PostGIS, and Redis:

```bash
docker compose up --build
```

Services:

- Web: http://localhost:3000
- API: http://localhost:8000
- API liveness: http://localhost:8000/health/live
- API readiness: http://localhost:8000/health/ready
- API version: http://localhost:8000/version
- Web login: http://localhost:3000/login
- Web signup: http://localhost:3000/signup
- Protected dashboard: http://localhost:3000/dashboard
- PostgreSQL: localhost:5432
- Redis: localhost:6379

## Farm Digital Twin Core

Phase 3A adds backend-first geospatial infrastructure. PostgreSQL runs with PostGIS enabled through `infrastructure/database/init/001_enable_postgis.sql`, and the geospatial Alembic migration also runs `CREATE EXTENSION IF NOT EXISTS postgis` for migrated environments.

Geospatial API routes:

- `POST /api/v1/farm-boundaries`
- `GET /api/v1/farm-boundaries/{id}`
- `POST /api/v1/plot-boundaries`
- `GET /api/v1/plot-boundaries/{id}`
- `GET /api/v1/geo-regions`

Boundary create requests accept GeoJSON `Polygon`, `Feature`, or single-polygon `FeatureCollection` payloads. The API validates coordinates and calculates square meters, hectares, and acres server-side.

Example:

```json
{
  "farm_id": 1,
  "geometry": {
    "type": "Polygon",
    "coordinates": [
      [
        [80.9462, 26.8467],
        [80.9472, 26.8467],
        [80.9472, 26.8477],
        [80.9462, 26.8477],
        [80.9462, 26.8467]
      ]
    ]
  }
}
```

## Mobile

Expo is usually run outside Docker:

```bash
pnpm mobile:start
```

Mobile authentication uses `@clerk/clerk-expo` with `expo-secure-store` token persistence. Set `EXPO_PUBLIC_CLERK_PUBLISHABLE_KEY` and `EXPO_PUBLIC_API_BASE_URL` in `apps/mobile/.env` before starting Expo. The app scheme is `krishiai`, which enables Expo Router deep linking.

Mobile routes:

- `/login`: email/password login
- `/signup`: email/password signup with email code verification
- `/dashboard`: protected dashboard
- `/profile`: protected editable profile
- `/onboarding/*`: protected onboarding routes

## Development Commands

```bash
pnpm web:dev
pnpm api:dev
pnpm mobile:start
pnpm typecheck
pnpm lint
pnpm build
```

For local API development outside Docker:

```bash
cd apps/api
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements-dev.txt
fastapi dev app/main.py --host 0.0.0.0 --port 8000
```

Run API tests when Python is available:

```bash
cd apps/api
pytest
```

## Assumptions

- The initial Docker stack runs web, API, PostGIS, and Redis. Mobile is started with Expo separately.
- External AI, Bhashini, and WhatsApp credentials are environment placeholders only.
- Alembic migrations are present for the Phase 2 authentication/RBAC schema and Phase 3A geospatial schema.
- API readiness currently confirms application readiness, not live database or Redis connectivity.
