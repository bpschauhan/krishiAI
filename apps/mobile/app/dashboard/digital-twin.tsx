import { useAuth } from "@clerk/clerk-expo";
import type { BoundaryFeatureProperties, FarmBoundary, PlotBoundary } from "@krishiai/shared-types";
import {
  createBoundaryExport,
  createBoundaryFeature,
  formatBoundaryArea,
  formatBoundaryHectares,
  formatBoundaryUpdatedAt,
  projectBoundariesToViewport
} from "@krishiai/shared-utils";
import { router } from "expo-router";
import { useCallback, useMemo, useState } from "react";
import { ActivityIndicator, Pressable, Share, StyleSheet, Text, View } from "react-native";
import Svg, { Polygon } from "react-native-svg";
import { ProtectedScreen } from "../../components/auth/protected-screen";
import { getFarmBoundaries, getPlotBoundaries } from "../../lib/digital-twin-api";
import { ActionButton, ButtonRow, Field, OnboardingScreen, styles as onboardingStyles } from "../onboarding/ui";

const MAP_WIDTH = 320;
const MAP_HEIGHT = 260;

export default function MobileDigitalTwinScreen() {
  const { getToken } = useAuth();
  const [farmId, setFarmId] = useState("1");
  const [plotId, setPlotId] = useState("1");
  const [farmBoundaries, setFarmBoundaries] = useState<FarmBoundary[]>([]);
  const [plotBoundaries, setPlotBoundaries] = useState<PlotBoundary[]>([]);
  const [showFarmBoundaries, setShowFarmBoundaries] = useState(true);
  const [showPlotBoundaries, setShowPlotBoundaries] = useState(true);
  const [selectedBoundary, setSelectedBoundary] = useState<BoundaryFeatureProperties | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const farmIdNumber = toPositiveInteger(farmId);
  const plotIdNumber = toPositiveInteger(plotId);
  const farmName = farmIdNumber ? `Farm #${farmIdNumber}` : "Selected farm";
  const plotName = plotIdNumber ? `Plot #${plotIdNumber}` : "Selected plot";

  const visibleFarmBoundaries = showFarmBoundaries ? farmBoundaries : [];
  const visiblePlotBoundaries = showPlotBoundaries ? plotBoundaries : [];
  const projectedBoundaries = useMemo(
    () =>
      projectBoundariesToViewport(
        [
          ...visibleFarmBoundaries.map((boundary) => ({ boundary, kind: "farm" as const })),
          ...visiblePlotBoundaries.map((boundary) => ({ boundary, kind: "plot" as const }))
        ],
        MAP_WIDTH,
        MAP_HEIGHT
      ),
    [visibleFarmBoundaries, visiblePlotBoundaries]
  );

  const loadBoundaries = useCallback(async () => {
    if (farmIdNumber === null || plotIdNumber === null) {
      setError("Farm and plot selectors must be positive IDs.");
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const token = await getToken();
      if (!token) {
        throw new Error("Missing Clerk session token");
      }

      const [nextFarmBoundaries, nextPlotBoundaries] = await Promise.all([
        getFarmBoundaries(token, farmIdNumber),
        getPlotBoundaries(token, plotIdNumber)
      ]);
      setFarmBoundaries(nextFarmBoundaries);
      setPlotBoundaries(nextPlotBoundaries);
      setSelectedBoundary(null);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Unable to load boundaries");
    } finally {
      setIsLoading(false);
    }
  }, [farmIdNumber, getToken, plotIdNumber]);

  async function exportGeoJson() {
    const payload = createBoundaryExport(visibleFarmBoundaries, visiblePlotBoundaries, { farmName, plotName });
    await Share.share({
      title: "KrishiAI boundary GeoJSON",
      message: payload
    });
  }

  function selectProjectedBoundary(id: number, kind: "farm" | "plot") {
    if (kind === "farm") {
      const boundary = farmBoundaries.find((item) => item.id === id);
      if (boundary) {
        setSelectedBoundary(createBoundaryFeature(boundary, "farm", farmName).properties);
      }
      return;
    }

    const boundary = plotBoundaries.find((item) => item.id === id);
    if (boundary) {
      setSelectedBoundary(createBoundaryFeature(boundary, "plot", plotName).properties);
    }
  }

  return (
    <ProtectedScreen requiredPermissions={["dashboard:read"]}>
      <OnboardingScreen eyebrow="Digital Twin" title="Boundary viewer">
        <View style={screenStyles.selectorGrid}>
          <Field label="Farm selector" keyboardType="number-pad" value={farmId} onChangeText={setFarmId} />
          <Field label="Plot selector" keyboardType="number-pad" value={plotId} onChangeText={setPlotId} />
        </View>

        <ButtonRow>
          <ActionButton label="Load" onPress={() => void loadBoundaries()} />
          <ActionButton label="Dashboard" variant="secondary" onPress={() => router.push("/dashboard")} />
        </ButtonRow>

        <ButtonRow>
          <Toggle checked={showFarmBoundaries} label="Farms" onPress={() => setShowFarmBoundaries((value) => !value)} />
          <Toggle checked={showPlotBoundaries} label="Plots" onPress={() => setShowPlotBoundaries((value) => !value)} />
        </ButtonRow>

        {isLoading ? (
          <View style={screenStyles.inlineState}>
            <ActivityIndicator color="#15803d" />
            <Text style={screenStyles.mutedText}>Loading boundary GeoJSON...</Text>
          </View>
        ) : null}

        {error ? <Text style={onboardingStyles.error}>{error}</Text> : null}

        <View style={screenStyles.mapFrame}>
          {projectedBoundaries.length === 0 ? (
            <Text style={screenStyles.emptyText}>No boundaries are available for the selected farm or plot yet.</Text>
          ) : (
            <Svg height={MAP_HEIGHT} width={MAP_WIDTH} viewBox={`0 0 ${MAP_WIDTH} ${MAP_HEIGHT}`}>
              {projectedBoundaries
                .filter((boundary) => boundary.kind === "farm")
                .map((boundary) => (
                  <Polygon
                    fill="#16a34a33"
                    key={`farm-${boundary.id}`}
                    onPress={() => selectProjectedBoundary(boundary.id, "farm")}
                    points={boundary.points}
                    stroke="#15803d"
                    strokeWidth={3}
                  />
                ))}
              {projectedBoundaries
                .filter((boundary) => boundary.kind === "plot")
                .map((boundary) => (
                  <Polygon
                    fill="#f59e0b55"
                    key={`plot-${boundary.id}`}
                    onPress={() => selectProjectedBoundary(boundary.id, "plot")}
                    points={boundary.points}
                    stroke="#b45309"
                    strokeWidth={2}
                  />
                ))}
            </Svg>
          )}
        </View>

        <BoundaryDetails selectedBoundary={selectedBoundary} />

        <ActionButton
          disabled={visibleFarmBoundaries.length + visiblePlotBoundaries.length === 0}
          label="Share GeoJSON"
          variant="secondary"
          onPress={() => void exportGeoJson()}
        />
      </OnboardingScreen>
    </ProtectedScreen>
  );
}

function Toggle({ checked, label, onPress }: { checked: boolean; label: string; onPress: () => void }) {
  return (
    <Pressable
      accessibilityRole="button"
      onPress={onPress}
      style={[screenStyles.toggle, checked ? screenStyles.toggleActive : null]}
    >
      <Text style={[screenStyles.toggleText, checked ? screenStyles.toggleTextActive : null]}>{label}</Text>
    </Pressable>
  );
}

function BoundaryDetails({ selectedBoundary }: { selectedBoundary: BoundaryFeatureProperties | null }) {
  if (!selectedBoundary) {
    return (
      <View style={screenStyles.detailsCard}>
        <Text style={screenStyles.detailsTitle}>Boundary details</Text>
        <Text style={screenStyles.mutedText}>Tap a visible farm or plot boundary to inspect it.</Text>
      </View>
    );
  }

  return (
    <View style={screenStyles.detailsCard}>
      <Text style={screenStyles.detailsTitle}>
        {selectedBoundary.boundaryKind === "farm" ? "Farm boundary" : "Plot boundary"}
      </Text>
      <Detail label={selectedBoundary.boundaryKind === "farm" ? "Farm name" : "Plot name"} value={selectedBoundary.ownerName} />
      <Detail label="Area acres" value={formatBoundaryArea(selectedBoundary.areaAcres)} />
      <Detail label="Area hectares" value={formatBoundaryHectares(selectedBoundary.areaHectares)} />
      <Detail label="Last updated" value={formatBoundaryUpdatedAt(selectedBoundary.updatedAt)} />
    </View>
  );
}

function Detail({ label, value }: { label: string; value: string }) {
  return (
    <View style={screenStyles.detailRow}>
      <Text style={screenStyles.detailLabel}>{label}</Text>
      <Text style={screenStyles.detailValue}>{value}</Text>
    </View>
  );
}

function toPositiveInteger(value: string): number | null {
  const parsed = Number.parseInt(value, 10);
  return Number.isInteger(parsed) && parsed > 0 ? parsed : null;
}

const screenStyles = StyleSheet.create({
  selectorGrid: {
    gap: 14
  },
  inlineState: {
    alignItems: "center",
    flexDirection: "row",
    gap: 10
  },
  mutedText: {
    color: "#64748b",
    fontSize: 14,
    lineHeight: 20
  },
  mapFrame: {
    alignItems: "center",
    justifyContent: "center",
    minHeight: MAP_HEIGHT,
    overflow: "hidden",
    borderWidth: 1,
    borderColor: "#cbd5e1",
    borderRadius: 8,
    backgroundColor: "#eef2f7"
  },
  emptyText: {
    maxWidth: 240,
    color: "#64748b",
    fontSize: 14,
    lineHeight: 20,
    textAlign: "center"
  },
  toggle: {
    minHeight: 42,
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    borderWidth: 1,
    borderColor: "#cbd5e1",
    borderRadius: 8,
    backgroundColor: "#ffffff"
  },
  toggleActive: {
    borderColor: "#15803d",
    backgroundColor: "#dcfce7"
  },
  toggleText: {
    color: "#334155",
    fontSize: 14,
    fontWeight: "700"
  },
  toggleTextActive: {
    color: "#166534"
  },
  detailsCard: {
    gap: 10,
    borderWidth: 1,
    borderColor: "#e2e8f0",
    borderRadius: 8,
    backgroundColor: "#ffffff",
    padding: 16
  },
  detailsTitle: {
    color: "#0f172a",
    fontSize: 15,
    fontWeight: "700"
  },
  detailRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    gap: 12
  },
  detailLabel: {
    color: "#64748b",
    fontSize: 13
  },
  detailValue: {
    maxWidth: 180,
    color: "#0f172a",
    fontSize: 13,
    fontWeight: "700",
    textAlign: "right"
  }
});
