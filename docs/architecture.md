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

## Farm Digital Twin Core

Phase 3A introduces backend geospatial infrastructure only. It does not include weather, satellite intelligence, AI recommendations, or map UI.

PostGIS is enabled in two places:

- Docker database initialization: `infrastructure/database/init/001_enable_postgis.sql`
- Alembic migration: `202606300001_geospatial_core.py`

Core models:

- `FarmBoundary`: links a farm to a PostGIS polygon and stores calculated square meters, hectares, and acres.
- `PlotBoundary`: links a plot to a PostGIS polygon and stores calculated square meters, hectares, and acres.
- `GeoRegion`: stores hierarchical administrative or operational regions with geometry.

GeoJSON handling is centralized in `app.utils.geo`. Accepted inputs are:

- GeoJSON `Polygon`
- GeoJSON `Feature` with `Polygon` geometry
- GeoJSON `FeatureCollection` containing exactly one polygon feature

The API validates ring closure, coordinate ranges, numeric coordinates, and polygon shape. Area is calculated server-side from submitted geometry; client-provided area values are ignored.

Geospatial routes are mounted under `/api/v1`:

- `POST /farm-boundaries`
- `GET /farm-boundaries/{id}`
- `PUT /farm-boundaries/{id}`
- `DELETE /farm-boundaries/{id}`
- `GET /farms/{farm_id}/boundaries`
- `POST /plot-boundaries`
- `GET /plot-boundaries/{id}`
- `PUT /plot-boundaries/{id}`
- `DELETE /plot-boundaries/{id}`
- `GET /plots/{plot_id}/boundaries`
- `GET /geo-regions`

## Boundary Management And Regions

Phase 3B adds the boundary lifecycle and region infrastructure on top of the Phase 3A geometry foundation.

- Boundary updates replace stored geometry and recalculate area server-side.
- Boundary deletes are hard deletes for the current lifecycle.
- Boundary listing APIs expose paginated farm and plot boundary collections.
- Region seeding is isolated from onboarding seed data and models a country, state, district, block, and village hierarchy with a small Uttar Pradesh example.
- Backend-only spatial helpers support point containment, intersection checks, bounding boxes, and region lookup.

## Digital Twin Viewer

Phase 3C introduces visualization only. It does not include weather, satellite intelligence, NDVI, analytics, AI recommendations, maps editing, or boundary mutation.

Web viewer:

- The protected route is `/dashboard/digital-twin`.
- Map rendering uses MapLibre GL with an OpenStreetMap raster style.
- Farm and plot boundary collections are fetched from `GET /api/v1/farms/{farm_id}/boundaries` and `GET /api/v1/plots/{plot_id}/boundaries`.
- Farm boundaries render as the lower visual layer; plot boundaries render above them.
- Shared utilities convert API boundary records into GeoJSON `FeatureCollection` objects, calculate bounds, format area values, and create export payloads.
- The details panel is read-only and shows owner label, acres, hectares, and last updated timestamp.

Mobile viewer:

- The protected Expo route is `/dashboard/digital-twin`.
- Mobile consumes the same boundary APIs and shared projection/export helpers.
- Rendering is read-only using projected GeoJSON polygons via `react-native-svg`.
- GeoJSON export uses the native share sheet.

## Spatial Intelligence Layer

Phase 3D is backend-only and builds spatial query services on top of stored farm boundaries, plot boundaries, and region geometries. It does not include weather, satellite imagery, NDVI, AI recommendations, analytics, or map editing.

Service layer:

- `point_in_polygon`: checks whether a longitude/latitude falls inside a polygon.
- `nearest_boundaries`: returns nearby farm boundaries, plot boundaries, and regions inside a radius.
- `intersecting_boundaries`: finds farm/farm, farm/plot, and plot/plot intersections.
- `region_resolver`: resolves the country, state, district, block, and village hierarchy for a farm or plot boundary.
- `bbox_search`: finds boundaries and regions intersecting a submitted bounding box.

PostgreSQL deployments use PostGIS functions such as `ST_Contains`, `ST_DWithin`, `ST_Intersects`, `ST_Centroid`, and `ST_Perimeter`. SQLite test runs use the Python fallback in `app.services.spatial_intelligence`, which reuses existing GeoJSON validation and polygon relation helpers.

Spatial APIs are mounted under `/api/v1/spatial`:

- `POST /point-lookup`: accepts longitude and latitude and returns containing farm boundaries, plot boundaries, and regions.
- `POST /nearby`: accepts longitude, latitude, and `radius_km`, then returns nearby farms, plots, and regions.
- `GET /intersections`: returns intersection metadata. Optional `relation_type` supports `farm/farm`, `farm/plot`, and `plot/plot`.
- `GET /farm/{farm_id}/regions`: resolves the administrative hierarchy for a farm boundary.
- `GET /plot/{plot_id}/regions`: resolves the administrative hierarchy for a plot boundary.
- `POST /bbox-search`: accepts `west`, `south`, `east`, and `north`, then returns intersecting farms, plots, and regions.

Spatial metrics are calculated on demand and are not persisted:

- Centroid longitude/latitude.
- Perimeter in meters.
- Compactness score, normalized from 0 to 1.

Example point lookup request:

```json
{
  "longitude": 80.94,
  "latitude": 26.97
}
```

Example nearby request:

```json
{
  "longitude": 80.94,
  "latitude": 26.97,
  "radius_km": 5
}
```

Example bounding box request:

```json
{
  "west": 80.91,
  "south": 26.94,
  "east": 80.97,
  "north": 27.0
}
```

## Weather Intelligence Foundation

Phase 4A is backend-first weather data infrastructure. It does not include AI recommendations, crop advice, disease prediction, irrigation advice, WhatsApp, or advisory workflows.

Weather persistence models:

- `WeatherLocation`: stores farm-derived or coordinate-derived lookup locations.
- `CurrentWeather`: stores current provider observations.
- `HourlyForecast`: stores hourly forecast rows.
- `DailyForecast`: stores daily forecast rows.
- `WeatherObservation`: stores historical weather observations.

All weather records support the core weather fields where available:

- Temperature.
- Humidity.
- Rainfall.
- Wind speed.
- Pressure.
- Cloud cover.

Provider layer:

- `WeatherProvider` defines current weather, hourly forecast, daily forecast, and historical weather methods.
- `OpenMeteoProvider` implements the provider contract.
- FastAPI routes do not contain provider-specific request or parsing logic.

Weather service:

- Resolves farm weather through `Farm -> FarmBoundary -> centroid -> provider lookup`.
- Persists fetched provider results into weather tables.
- Uses Redis cache when reachable and an in-memory fallback otherwise.
- Provides reusable sync methods for current weather and forecasts; no scheduler is installed in Phase 4A.

Weather APIs are mounted under `/api/v1/weather`:

- `GET /current`: accepts `farm_id` or coordinates and returns current weather.
- `GET /hourly`: accepts `farm_id` or coordinates plus `hours`.
- `GET /daily`: accepts `farm_id` or coordinates plus `days`.
- `GET /history`: accepts `farm_id` or coordinates plus optional `start_date` and `end_date`.

Example current weather request:

```text
GET /api/v1/weather/current?farm_id=1
```

Example history request:

```text
GET /api/v1/weather/history?farm_id=1&start_date=2026-06-30&end_date=2026-06-30
```
