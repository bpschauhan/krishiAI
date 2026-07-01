import type { FarmBoundary, PlotBoundary } from "@krishiai/shared-types";
import {
  createBoundaryFeatureCollection,
  createBoundaryExport,
  getBoundaryBounds,
  projectBoundariesToViewport
} from "./index";

const farmBoundary: FarmBoundary = {
  id: 1,
  farm_id: 10,
  geometry: {
    type: "Polygon",
    coordinates: [[[80, 26], [81, 26], [81, 27], [80, 27], [80, 26]]]
  },
  area_square_meters: "10000",
  area_hectares: "1",
  area_acres: "2.47",
  created_at: "2026-07-01T00:00:00Z",
  updated_at: "2026-07-01T00:00:00Z"
};

const plotBoundary: PlotBoundary = {
  id: 2,
  plot_id: 20,
  geometry: {
    type: "Polygon",
    coordinates: [[[80.2, 26.2], [80.6, 26.2], [80.6, 26.6], [80.2, 26.6], [80.2, 26.2]]]
  },
  area_square_meters: 5000,
  area_hectares: 0.5,
  area_acres: 1.24,
  created_at: "2026-07-01T00:00:00Z",
  updated_at: "2026-07-01T00:00:00Z"
};

function assert(condition: boolean, message: string): void {
  if (!condition) {
    throw new Error(message);
  }
}

const collection = createBoundaryFeatureCollection([farmBoundary], [plotBoundary]);
assert(collection.features.length === 2, "feature collection should include farm and plot boundaries");
assert(collection.features[1]?.properties.boundaryKind === "plot", "plot boundary should be preserved");

const bounds = getBoundaryBounds([farmBoundary, plotBoundary]);
assert(bounds?.[0][0] === 80, "bounds should include west longitude");
assert(bounds?.[1][1] === 27, "bounds should include north latitude");

const projected = projectBoundariesToViewport(
  [
    { boundary: farmBoundary, kind: "farm" },
    { boundary: plotBoundary, kind: "plot" }
  ],
  320,
  220
);
assert(projected.length === 2, "projection should create drawable boundaries");
assert(projected.every((item) => item.points.length > 0), "projection should emit polygon points");

const geoJson = createBoundaryExport([farmBoundary], [plotBoundary]);
assert(geoJson.includes("\"FeatureCollection\""), "export should emit GeoJSON");
