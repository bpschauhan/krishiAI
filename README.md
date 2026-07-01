# KrishiAI

KrishiAI is a production-grade monorepo foundation for an AI-powered agricultural operating system focused on farmers in Uttar Pradesh, India.

The current implementation includes onboarding, authentication, Farm Digital Twin infrastructure, spatial intelligence, weather intelligence, disease risk scoring, and water requirement assessment.

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
- Maps: MapLibre GL for web boundary visualization
- Weather: Open-Meteo provider integration with Redis-backed caching and database persistence
- Water: Crop-stage water profiles with farm-level requirement, deficit, and surplus assessment

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
- Digital Twin viewer: http://localhost:3000/dashboard/digital-twin
- PostgreSQL: localhost:5432
- Redis: localhost:6379

## Farm Digital Twin Core

Phase 3A adds backend-first geospatial infrastructure. PostgreSQL runs with PostGIS enabled through `infrastructure/database/init/001_enable_postgis.sql`, and the geospatial Alembic migration also runs `CREATE EXTENSION IF NOT EXISTS postgis` for migrated environments.

Geospatial API routes:

- `POST /api/v1/farm-boundaries`
- `GET /api/v1/farm-boundaries/{id}`
- `PUT /api/v1/farm-boundaries/{id}`
- `DELETE /api/v1/farm-boundaries/{id}`
- `GET /api/v1/farms/{farm_id}/boundaries`
- `POST /api/v1/plot-boundaries`
- `GET /api/v1/plot-boundaries/{id}`
- `PUT /api/v1/plot-boundaries/{id}`
- `DELETE /api/v1/plot-boundaries/{id}`
- `GET /api/v1/plots/{plot_id}/boundaries`
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

## Digital Twin Viewer

Phase 3C adds rendering-only farm and plot boundary visualization.

Web:

- `/dashboard/digital-twin` renders farm boundaries and plot boundaries with MapLibre GL.
- Plot layers render above farm layers.
- The viewer supports farm and plot ID selectors, boundary visibility toggles, zoom to visible boundaries, empty states, read-only details, and GeoJSON download.
- Boundary data is loaded from existing APIs only: `GET /api/v1/farms/{farm_id}/boundaries` and `GET /api/v1/plots/{plot_id}/boundaries`.

Mobile:

- `/dashboard/digital-twin` provides a protected read-only Expo viewer.
- The mobile viewer renders projected GeoJSON polygons with `react-native-svg`, displays boundary details, and shares GeoJSON through the native share sheet.

This phase does not include weather, satellite intelligence, NDVI, analytics, AI recommendations, or boundary editing.

## Spatial Intelligence Layer

Phase 3D adds backend-only spatial intelligence APIs on top of existing farm, plot, and region boundaries. It does not add weather, satellite imagery, NDVI, AI recommendations, or map editing.

Spatial APIs:

- `POST /api/v1/spatial/point-lookup`
- `POST /api/v1/spatial/nearby`
- `GET /api/v1/spatial/intersections`
- `GET /api/v1/spatial/farm/{farm_id}/regions`
- `GET /api/v1/spatial/plot/{plot_id}/regions`
- `POST /api/v1/spatial/bbox-search`

Point lookup example:

```json
{
  "longitude": 80.94,
  "latitude": 26.97
}
```

Nearby search example:

```json
{
  "longitude": 80.94,
  "latitude": 26.97,
  "radius_km": 5
}
```

Bounding box search example:

```json
{
  "west": 80.91,
  "south": 26.94,
  "east": 80.97,
  "north": 27.0
}
```

Responses include matching farm boundaries, plot boundaries, regions, and on-demand spatial metrics: centroid, perimeter, and compactness score. PostgreSQL uses PostGIS operations; tests remain SQLite-compatible through the Python spatial service fallback.

## Weather Intelligence Foundation

Phase 4A adds backend-first weather data infrastructure. It does not include AI recommendations, crop advice, disease prediction, irrigation advice, or WhatsApp delivery.

Weather data models:

- `WeatherLocation`
- `CurrentWeather`
- `HourlyForecast`
- `DailyForecast`
- `WeatherObservation`

The provider layer exposes a `WeatherProvider` interface and an `OpenMeteoProvider` implementation. Route handlers call the weather service only; provider-specific API logic stays out of FastAPI routes.

Weather APIs:

- `GET /api/v1/weather/current?farm_id=1`
- `GET /api/v1/weather/hourly?farm_id=1&hours=24`
- `GET /api/v1/weather/daily?farm_id=1&days=7`
- `GET /api/v1/weather/history?farm_id=1&start_date=2026-06-30&end_date=2026-06-30`

Farm weather resolution uses existing Farm Digital Twin geometry:

```text
Farm -> FarmBoundary -> centroid -> weather lookup
```

Each response supports temperature, humidity, rainfall, wind speed, pressure, and cloud cover when those values are available from the provider. Results are cached through Redis when available and fall back to in-memory cache otherwise. Fetched data is persisted for the weather data platform.

## Disease Risk Engine

Phase 4B adds deterministic disease risk scoring from crop, growth stage, and weather conditions. It does not include crop recommendations, AI chat, WhatsApp, irrigation advice, fertilizer advice, treatment plans, or advisory text.

Catalog models:

- `Crop`
- `CropDisease`
- `CropStage`
- `DiseaseRiskAssessment`

The seed framework includes an extensible starter disease library:

- Rice: Blast, Brown Spot
- Wheat: Rust
- Potato: Late Blight
- Sugarcane: Red Rot

Risk API:

```text
GET /api/v1/disease-risk?farm_id=1&crop_id=1&crop_stage_id=1
```

Risk levels:

- `0-30`: Low
- `31-70`: Medium
- `71-100`: High

The response includes aggregate `risk_score`, `risk_level`, and per-disease results with contributing factors. Assessments are stored in `DiseaseRiskAssessment` for history.

## Water Intelligence Foundation

Phase 4C adds backend-first water requirement assessment. It measures crop-stage water need against available weather rainfall data. It does not include irrigation schedules, irrigation recommendations, pump control, crop recommendations, AI advisory, or WhatsApp delivery.

Water models:

- `CropWaterProfile`
- `FarmWaterRequirement`
- `WaterAssessmentHistory`

The water profile seed framework includes extensible starter profiles for Rice, Wheat, Potato, and Sugarcane, with growth-stage-specific minimum, optimal, and maximum millimeters per day.

Water API:

```text
GET /api/v1/water-intelligence?farm_id=1&crop_id=1&crop_stage_id=1
```

Response shape:

```json
{
  "estimated_requirement_mm": "7.70",
  "rainfall_mm": "2.00",
  "deficit_mm": "5.70",
  "surplus_mm": "0.00",
  "status": "Deficit"
}
```

Status levels:

- `Adequate`: rainfall and requirement are balanced within tolerance.
- `Deficit`: estimated requirement exceeds rainfall.
- `Surplus`: rainfall exceeds estimated requirement.

Calculation methodology:

```text
Farm -> FarmBoundary -> WeatherLocation/current weather -> crop water profile -> water assessment
```

The engine starts from the crop-stage optimal water profile, adjusts for high or low temperature, clamps the result between the profile minimum and maximum, then compares it with rainfall. Results are stored in both the current requirement table and the assessment history table.

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
- `/dashboard/digital-twin`: protected read-only Digital Twin boundary viewer
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
- Alembic migrations are present for authentication/RBAC, geospatial, boundary lifecycle, weather foundation, and disease risk schema.
- API readiness currently confirms application readiness, not live database or Redis connectivity.
