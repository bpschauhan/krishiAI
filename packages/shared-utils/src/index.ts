import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import type {
  BoundaryFeatureProperties,
  BoundaryKind,
  BoundaryRecord,
  FarmBoundary,
  GeoJsonFeature,
  GeoJsonFeatureCollection,
  GeoJsonPolygon,
  GeoJsonPosition,
  HealthStatus,
  PlotBoundary
} from "@krishiai/shared-types";

export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

export function formatServiceStatus(health: HealthStatus): string {
  return `${health.service}: ${health.status}`;
}

export type BoundaryBounds = [[number, number], [number, number]];

export type ProjectedBoundary = {
  id: number;
  kind: BoundaryKind;
  points: string;
};

export function createBoundaryFeature(
  boundary: FarmBoundary,
  kind: "farm",
  ownerName?: string
): GeoJsonFeature<BoundaryFeatureProperties>;
export function createBoundaryFeature(
  boundary: PlotBoundary,
  kind: "plot",
  ownerName?: string
): GeoJsonFeature<BoundaryFeatureProperties>;
export function createBoundaryFeature(
  boundary: BoundaryRecord,
  kind: BoundaryKind,
  ownerName?: string
): GeoJsonFeature<BoundaryFeatureProperties> {
  const isFarm = kind === "farm";
  const ownerId = isFarm ? (boundary as FarmBoundary).farm_id : (boundary as PlotBoundary).plot_id;
  const fallbackName = isFarm ? `Farm #${ownerId}` : `Plot #${ownerId}`;

  return {
    type: "Feature",
    geometry: boundary.geometry,
    properties: {
      boundaryKind: kind,
      id: boundary.id,
      ownerId,
      ownerName: ownerName ?? fallbackName,
      areaAcres: toNumber(boundary.area_acres),
      areaHectares: toNumber(boundary.area_hectares),
      updatedAt: boundary.updated_at
    }
  };
}

export function createBoundaryFeatureCollection(
  farmBoundaries: FarmBoundary[],
  plotBoundaries: PlotBoundary[],
  names: { farmName?: string; plotName?: string } = {}
): GeoJsonFeatureCollection<BoundaryFeatureProperties> {
  return {
    type: "FeatureCollection",
    features: [
      ...farmBoundaries.map((boundary) => createBoundaryFeature(boundary, "farm", names.farmName)),
      ...plotBoundaries.map((boundary) => createBoundaryFeature(boundary, "plot", names.plotName))
    ]
  };
}

export function createBoundaryExport(
  farmBoundaries: FarmBoundary[],
  plotBoundaries: PlotBoundary[],
  names: { farmName?: string; plotName?: string } = {}
): string {
  return `${JSON.stringify(createBoundaryFeatureCollection(farmBoundaries, plotBoundaries, names), null, 2)}\n`;
}

export function getBoundaryBounds(boundaries: BoundaryRecord[]): BoundaryBounds | null {
  const positions = boundaries.flatMap((boundary) => getPolygonPositions(boundary.geometry));
  if (positions.length === 0) {
    return null;
  }

  const longitudes = positions.map((position) => position[0]);
  const latitudes = positions.map((position) => position[1]);
  return [
    [Math.min(...longitudes), Math.min(...latitudes)],
    [Math.max(...longitudes), Math.max(...latitudes)]
  ];
}

export function projectBoundariesToViewport(
  boundaries: Array<{ boundary: BoundaryRecord; kind: BoundaryKind }>,
  width: number,
  height: number,
  padding = 16
): ProjectedBoundary[] {
  const bounds = getBoundaryBounds(boundaries.map((item) => item.boundary));
  if (!bounds) {
    return [];
  }

  const [[west, south], [east, north]] = bounds;
  const longitudeSpan = Math.max(east - west, 0.000001);
  const latitudeSpan = Math.max(north - south, 0.000001);
  const drawableWidth = Math.max(width - padding * 2, 1);
  const drawableHeight = Math.max(height - padding * 2, 1);

  return boundaries.map(({ boundary, kind }) => {
    const ring = boundary.geometry.coordinates[0] ?? [];
    const points = ring
      .map((position) => {
        const x = padding + ((position[0] - west) / longitudeSpan) * drawableWidth;
        const y = padding + ((north - position[1]) / latitudeSpan) * drawableHeight;
        return `${roundForDisplay(x)},${roundForDisplay(y)}`;
      })
      .join(" ");

    return { id: boundary.id, kind, points };
  });
}

export function formatBoundaryArea(value: string | number): string {
  return `${toNumber(value).toFixed(2)} acres`;
}

export function formatBoundaryHectares(value: string | number): string {
  return `${toNumber(value).toFixed(2)} ha`;
}

export function formatBoundaryUpdatedAt(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "Unknown";
  }
  return new Intl.DateTimeFormat("en-IN", {
    dateStyle: "medium",
    timeStyle: "short"
  }).format(date);
}

function getPolygonPositions(polygon: GeoJsonPolygon): GeoJsonPosition[] {
  return polygon.coordinates.flat();
}

function toNumber(value: string | number): number {
  const parsed = typeof value === "number" ? value : Number.parseFloat(value);
  return Number.isFinite(parsed) ? parsed : 0;
}

function roundForDisplay(value: number): number {
  return Math.round(value * 100) / 100;
}
