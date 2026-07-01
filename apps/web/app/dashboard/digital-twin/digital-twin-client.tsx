"use client";

import { useAuth } from "@clerk/nextjs";
import type { BoundaryFeatureProperties } from "@krishiai/shared-types";
import { createBoundaryExport } from "@krishiai/shared-utils";
import { Button, Card, Input, Label } from "@krishiai/ui";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useMemo, useState } from "react";
import { BoundaryDetailsPanel } from "../../../components/digital-twin/boundary-details-panel";
import { BoundaryMap } from "../../../components/digital-twin/boundary-map";
import { getFarmBoundaries, getPlotBoundaries } from "../../../lib/digital-twin-api";

export function DigitalTwinClient() {
  const { getToken, isLoaded } = useAuth();
  const [farmId, setFarmId] = useState("1");
  const [plotId, setPlotId] = useState("1");
  const [showFarmBoundaries, setShowFarmBoundaries] = useState(true);
  const [showPlotBoundaries, setShowPlotBoundaries] = useState(true);
  const [selectedBoundary, setSelectedBoundary] = useState<BoundaryFeatureProperties | null>(null);
  const [zoomRequest, setZoomRequest] = useState(0);

  const farmIdNumber = toPositiveInteger(farmId);
  const plotIdNumber = toPositiveInteger(plotId);
  const canLoadFarm = isLoaded && farmIdNumber !== null;
  const canLoadPlot = isLoaded && plotIdNumber !== null;

  const farmQuery = useQuery({
    queryKey: ["farm-boundaries", farmIdNumber],
    enabled: canLoadFarm,
    queryFn: async () => {
      const token = await getToken();
      if (!token || farmIdNumber === null) {
        throw new Error("Missing session or farm id");
      }
      return getFarmBoundaries(token, farmIdNumber, { limit: 100 });
    }
  });

  const plotQuery = useQuery({
    queryKey: ["plot-boundaries", plotIdNumber],
    enabled: canLoadPlot,
    queryFn: async () => {
      const token = await getToken();
      if (!token || plotIdNumber === null) {
        throw new Error("Missing session or plot id");
      }
      return getPlotBoundaries(token, plotIdNumber, { limit: 100 });
    }
  });

  const farmBoundaries = farmQuery.data ?? [];
  const plotBoundaries = plotQuery.data ?? [];
  const farmName = farmIdNumber ? `Farm #${farmIdNumber}` : "Selected farm";
  const plotName = plotIdNumber ? `Plot #${plotIdNumber}` : "Selected plot";
  const isLoading = farmQuery.isLoading || plotQuery.isLoading;
  const errorMessage = farmQuery.error?.message ?? plotQuery.error?.message;
  const exportPayload = useMemo(
    () => createBoundaryExport(showFarmBoundaries ? farmBoundaries : [], showPlotBoundaries ? plotBoundaries : [], { farmName, plotName }),
    [farmBoundaries, farmName, plotBoundaries, plotName, showFarmBoundaries, showPlotBoundaries]
  );

  function exportGeoJson() {
    const blob = new Blob([exportPayload], { type: "application/geo+json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `krishiai-digital-twin-farm-${farmIdNumber ?? "unknown"}-plot-${plotIdNumber ?? "unknown"}.geojson`;
    link.click();
    URL.revokeObjectURL(url);
  }

  return (
    <main className="min-h-screen bg-background px-5 py-8">
      <section className="mx-auto flex w-full max-w-7xl flex-col gap-6">
        <header className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div className="space-y-2">
            <p className="text-sm font-medium text-muted-foreground">Digital Twin Viewer</p>
            <h1 className="text-3xl font-semibold text-foreground">Farm and plot boundaries</h1>
          </div>
          <div className="flex flex-wrap gap-3">
            <Button variant="secondary">
              <Link href="/dashboard">Dashboard</Link>
            </Button>
            <Button type="button" variant="secondary" onClick={() => setZoomRequest((value) => value + 1)}>
              Zoom to boundary
            </Button>
            <Button type="button" onClick={exportGeoJson} disabled={farmBoundaries.length + plotBoundaries.length === 0}>
              Export GeoJSON
            </Button>
          </div>
        </header>

        <Card className="p-5">
          <div className="grid gap-4 lg:grid-cols-[1fr_1fr_auto_auto] lg:items-end">
            <div className="space-y-2">
              <Label htmlFor="farm-id">Farm selector</Label>
              <Input id="farm-id" min={1} type="number" value={farmId} onChange={(event) => setFarmId(event.target.value)} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="plot-id">Plot selector</Label>
              <Input id="plot-id" min={1} type="number" value={plotId} onChange={(event) => setPlotId(event.target.value)} />
            </div>
            <Toggle
              checked={showFarmBoundaries}
              label="Farm boundaries"
              onChange={(checked) => setShowFarmBoundaries(checked)}
            />
            <Toggle
              checked={showPlotBoundaries}
              label="Plot boundaries"
              onChange={(checked) => setShowPlotBoundaries(checked)}
            />
          </div>
          {farmIdNumber === null || plotIdNumber === null ? (
            <p className="mt-3 text-sm text-red-600">Farm and plot selectors must be positive IDs.</p>
          ) : null}
        </Card>

        {isLoading ? (
          <Card className="p-5">
            <p className="text-sm text-muted-foreground">Loading boundary GeoJSON...</p>
          </Card>
        ) : null}

        {errorMessage ? (
          <Card className="p-5">
            <p className="text-sm text-red-600">{errorMessage}</p>
          </Card>
        ) : null}

        <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_340px]">
          <BoundaryMap
            farmBoundaries={showFarmBoundaries ? farmBoundaries : []}
            plotBoundaries={showPlotBoundaries ? plotBoundaries : []}
            farmName={farmName}
            plotName={plotName}
            showFarmBoundaries={showFarmBoundaries}
            showPlotBoundaries={showPlotBoundaries}
            zoomRequest={zoomRequest}
            onSelectBoundary={setSelectedBoundary}
          />
          <BoundaryDetailsPanel selectedBoundary={selectedBoundary} />
        </div>
      </section>
    </main>
  );
}

function Toggle({
  checked,
  label,
  onChange
}: {
  checked: boolean;
  label: string;
  onChange: (checked: boolean) => void;
}) {
  return (
    <label className="flex min-h-10 items-center gap-2 rounded-md border border-border px-3 text-sm font-medium text-foreground">
      <input
        checked={checked}
        className="h-4 w-4 accent-green-700"
        type="checkbox"
        onChange={(event) => onChange(event.target.checked)}
      />
      {label}
    </label>
  );
}

function toPositiveInteger(value: string): number | null {
  const parsed = Number.parseInt(value, 10);
  return Number.isInteger(parsed) && parsed > 0 ? parsed : null;
}
