import type { FarmBoundary, PlotBoundary } from "@krishiai/shared-types";
import { apiRequest } from "./auth-api";

export function getFarmBoundaries(
  token: string,
  farmId: number,
  params: { offset?: number; limit?: number } = {}
): Promise<FarmBoundary[]> {
  return apiRequest<FarmBoundary[]>(`/api/v1/farms/${farmId}/boundaries${toQueryString(params)}`, token);
}

export function getPlotBoundaries(
  token: string,
  plotId: number,
  params: { offset?: number; limit?: number } = {}
): Promise<PlotBoundary[]> {
  return apiRequest<PlotBoundary[]>(`/api/v1/plots/${plotId}/boundaries${toQueryString(params)}`, token);
}

function toQueryString(params: { offset?: number; limit?: number }): string {
  const query = new URLSearchParams();
  if (params.offset !== undefined) {
    query.set("offset", String(params.offset));
  }
  if (params.limit !== undefined) {
    query.set("limit", String(params.limit));
  }
  const value = query.toString();
  return value ? `?${value}` : "";
}
