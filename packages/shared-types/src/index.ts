export type ServiceStatus = "ok" | "alive" | "ready" | "degraded";

export interface HealthStatus {
  status: ServiceStatus;
  service: string;
}

export interface VersionInfo {
  service: string;
  version: string;
}

export type GeoJsonPosition = [number, number] | [number, number, number];

export interface GeoJsonPolygon {
  type: "Polygon";
  coordinates: GeoJsonPosition[][];
}

export interface GeoJsonFeature<TProperties extends object = Record<string, unknown>> {
  type: "Feature";
  geometry: GeoJsonPolygon;
  properties: TProperties;
}

export interface GeoJsonFeatureCollection<
  TProperties extends object = Record<string, unknown>
> {
  type: "FeatureCollection";
  features: Array<GeoJsonFeature<TProperties>>;
}

export type BoundaryKind = "farm" | "plot";

export interface FarmBoundary {
  id: number;
  farm_id: number;
  geometry: GeoJsonPolygon;
  area_square_meters: string | number;
  area_hectares: string | number;
  area_acres: string | number;
  created_at: string;
  updated_at: string;
}

export interface PlotBoundary {
  id: number;
  plot_id: number;
  geometry: GeoJsonPolygon;
  area_square_meters: string | number;
  area_hectares: string | number;
  area_acres: string | number;
  created_at: string;
  updated_at: string;
}

export type BoundaryRecord = FarmBoundary | PlotBoundary;

export interface BoundaryFeatureProperties {
  boundaryKind: BoundaryKind;
  id: number;
  ownerId: number;
  ownerName: string;
  areaAcres: number;
  areaHectares: number;
  updatedAt: string;
}
