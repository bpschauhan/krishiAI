# KrishiAI

KrishiAI is a production-grade monorepo foundation for an AI-powered agricultural operating system focused on farmers in Uttar Pradesh, India.

This repository intentionally contains platform scaffolding only. There is no business logic, authentication, or AI workflow implementation yet.

## Stack

- Web: Next.js 15, TypeScript, Tailwind CSS, shadcn/ui conventions
- Mobile: React Native, Expo, TypeScript
- API: FastAPI, Python 3.13
- Database: PostgreSQL with PostGIS
- Cache: Redis
- Infrastructure: Docker and Docker Compose
- Monorepo: pnpm workspaces

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
- PostgreSQL: localhost:5432
- Redis: localhost:6379

## Mobile

Expo is usually run outside Docker:

```bash
pnpm mobile:start
```

## Development Commands

```bash
pnpm web:dev
pnpm api:dev
pnpm mobile:start
pnpm typecheck
```

For local API development outside Docker:

```bash
cd apps/api
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements-dev.txt
fastapi dev app/main.py --host 0.0.0.0 --port 8000
```

## Assumptions

- The initial Docker stack runs web, API, PostGIS, and Redis. Mobile is started with Expo separately.
- External AI, Bhashini, and WhatsApp credentials are environment placeholders only.
- Database migrations are not included yet because no domain schema exists.
- API readiness currently confirms application readiness, not live database or Redis connectivity.
