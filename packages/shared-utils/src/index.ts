import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import type { HealthStatus } from "@krishiai/shared-types";

export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

export function formatServiceStatus(health: HealthStatus): string {
  return `${health.service}: ${health.status}`;
}
