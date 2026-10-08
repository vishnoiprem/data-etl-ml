import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export const STRATEGY_COLORS: Record<string, string> = {
  vector: "#22d3ee",   // cyan-400
  bm25: "#f43f5e",     // rose-500
  graph: "#a855f7",    // purple-500
  hybrid: "#8b5cf6",   // violet-500
};
