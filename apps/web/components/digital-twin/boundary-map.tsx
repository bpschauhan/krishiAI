"use client";

import type {
  BoundaryFeatureProperties,
  FarmBoundary,
  GeoJsonFeatureCollection,
  PlotBoundary
} from "@krishiai/shared-types";
import {
  createBoundaryFeature,
  createBoundaryFeatureCollection,
  getBoundaryBounds
} from "@krishiai/shared-utils";
import maplibregl, {
  type GeoJSONSource,
  type LngLatBoundsLike,
  type MapLayerMouseEvent,
  type Map as MapLibreMap,
  type StyleSpecification
} from "maplibre-gl";
import { useEffect, useMemo, useRef, useState } from "react";

type BoundaryMapProps = {
  farmBoundaries: FarmBoundary[];
  plotBoundaries: PlotBoundary[];
  farmName: string;
  plotName: string;
  showFarmBoundaries: boolean;
  showPlotBoundaries: boolean;
  zoomRequest: number;
  onSelectBoundary: (boundary: BoundaryFeatureProperties) => void;
};

const EMPTY_COLLECTION: GeoJsonFeatureCollection<BoundaryFeatureProperties> = {
  type: "FeatureCollection",
  features: []
};

const MAP_STYLE: StyleSpecification = {
  version: 8,
  sources: {
    osm: {
      type: "raster",
      tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],
      tileSize: 256,
      attribution: "OpenStreetMap contributors"
    }
  },
  layers: [
    {
      id: "osm",
      type: "raster",
      source: "osm"
    }
  ]
};

export function BoundaryMap({
  farmBoundaries,
  plotBoundaries,
  farmName,
  plotName,
  showFarmBoundaries,
  showPlotBoundaries,
  zoomRequest,
  onSelectBoundary
}: BoundaryMapProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<MapLibreMap | null>(null);
  const [isReady, setIsReady] = useState(false);

  const farmCollection = useMemo<GeoJsonFeatureCollection<BoundaryFeatureProperties>>(
    () => ({
      type: "FeatureCollection",
      features: farmBoundaries.map((boundary) => createBoundaryFeature(boundary, "farm", farmName))
    }),
    [farmBoundaries, farmName]
  );
  const plotCollection = useMemo<GeoJsonFeatureCollection<BoundaryFeatureProperties>>(
    () => ({
      type: "FeatureCollection",
      features: plotBoundaries.map((boundary) => createBoundaryFeature(boundary, "plot", plotName))
    }),
    [plotBoundaries, plotName]
  );
  const combinedCollection = useMemo(
    () => createBoundaryFeatureCollection(farmBoundaries, plotBoundaries, { farmName, plotName }),
    [farmBoundaries, farmName, plotBoundaries, plotName]
  );

  useEffect(() => {
    if (!containerRef.current || mapRef.current) {
      return;
    }

    const map = new maplibregl.Map({
      container: containerRef.current,
      style: MAP_STYLE,
      center: [80.9462, 26.8467],
      zoom: 12,
      attributionControl: false
    });

    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");
    map.addControl(new maplibregl.AttributionControl({ compact: true }), "bottom-right");

    map.on("load", () => {
      map.addSource("farm-boundaries", {
        type: "geojson",
        data: EMPTY_COLLECTION
      });
      map.addLayer({
        id: "farm-boundary-fill",
        type: "fill",
        source: "farm-boundaries",
        paint: {
          "fill-color": "#16a34a",
          "fill-opacity": 0.16
        }
      });
      map.addLayer({
        id: "farm-boundary-line",
        type: "line",
        source: "farm-boundaries",
        paint: {
          "line-color": "#15803d",
          "line-width": 3
        }
      });

      map.addSource("plot-boundaries", {
        type: "geojson",
        data: EMPTY_COLLECTION
      });
      map.addLayer({
        id: "plot-boundary-fill",
        type: "fill",
        source: "plot-boundaries",
        paint: {
          "fill-color": "#f59e0b",
          "fill-opacity": 0.26
        }
      });
      map.addLayer({
        id: "plot-boundary-line",
        type: "line",
        source: "plot-boundaries",
        paint: {
          "line-color": "#b45309",
          "line-width": 2
        }
      });

      const handleBoundaryClick = (event: MapLayerMouseEvent) => {
        const properties = event.features?.[0]?.properties;
        if (!properties) {
          return;
        }
        onSelectBoundary({
          boundaryKind: properties.boundaryKind,
          id: Number(properties.id),
          ownerId: Number(properties.ownerId),
          ownerName: String(properties.ownerName),
          areaAcres: Number(properties.areaAcres),
          areaHectares: Number(properties.areaHectares),
          updatedAt: String(properties.updatedAt)
        });
      };

      map.on("click", "farm-boundary-fill", handleBoundaryClick);
      map.on("click", "plot-boundary-fill", handleBoundaryClick);
      map.on("mouseenter", "farm-boundary-fill", () => {
        map.getCanvas().style.cursor = "pointer";
      });
      map.on("mouseenter", "plot-boundary-fill", () => {
        map.getCanvas().style.cursor = "pointer";
      });
      map.on("mouseleave", "farm-boundary-fill", () => {
        map.getCanvas().style.cursor = "";
      });
      map.on("mouseleave", "plot-boundary-fill", () => {
        map.getCanvas().style.cursor = "";
      });

      setIsReady(true);
    });

    mapRef.current = map;

    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, [onSelectBoundary]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !isReady) {
      return;
    }

    (map.getSource("farm-boundaries") as GeoJSONSource).setData(
      showFarmBoundaries ? farmCollection : EMPTY_COLLECTION
    );
    (map.getSource("plot-boundaries") as GeoJSONSource).setData(
      showPlotBoundaries ? plotCollection : EMPTY_COLLECTION
    );
  }, [farmCollection, isReady, plotCollection, showFarmBoundaries, showPlotBoundaries]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !isReady) {
      return;
    }

    const visibleBoundaries = [
      ...(showFarmBoundaries ? farmBoundaries : []),
      ...(showPlotBoundaries ? plotBoundaries : [])
    ];
    const bounds = getBoundaryBounds(visibleBoundaries);
    if (!bounds) {
      return;
    }
    map.fitBounds(bounds as LngLatBoundsLike, { padding: 56, maxZoom: 17, duration: 650 });
  }, [combinedCollection, farmBoundaries, isReady, plotBoundaries, showFarmBoundaries, showPlotBoundaries, zoomRequest]);

  return (
    <div className="relative min-h-[520px] overflow-hidden rounded-lg border border-border bg-muted">
      <div ref={containerRef} className="absolute inset-0" />
      {combinedCollection.features.length === 0 ? (
        <div className="absolute inset-0 flex items-center justify-center bg-background/85 px-6 text-center">
          <p className="max-w-sm text-sm text-muted-foreground">
            No boundaries are available for the selected farm or plot yet.
          </p>
        </div>
      ) : null}
    </div>
  );
}
