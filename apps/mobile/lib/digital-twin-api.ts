import type { FarmBoundary, PlotBoundary } from "@krishiai/shared-types";

const apiBaseUrl = process.env.EXPO_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

async function apiRequest<T>(path: string, token: string): Promise<T> {
  const response = await fetch(`${apiBaseUrl}${path}`, {
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`
    }
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed with status ${response.status}`);
  }

  return (await response.json()) as T;
}

export function getFarmBoundaries(token: string, farmId: number): Promise<FarmBoundary[]> {
  return apiRequest<FarmBoundary[]>(`/api/v1/farms/${farmId}/boundaries?limit=100`, token);
}

export function getPlotBoundaries(token: string, plotId: number): Promise<PlotBoundary[]> {
  return apiRequest<PlotBoundary[]>(`/api/v1/plots/${plotId}/boundaries?limit=100`, token);
}
