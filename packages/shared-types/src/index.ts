export type ServiceStatus = "ok" | "alive" | "ready" | "degraded";

export interface HealthStatus {
  status: ServiceStatus;
  service: string;
}

export interface VersionInfo {
  service: string;
  version: string;
}
