import { STRATEGY_COLORS } from "@/lib/utils";

export function StrategyBadge({ strategy }: { strategy: string }) {
  const color = STRATEGY_COLORS[strategy] ?? "#999";
  return (
    <span
      className="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold"
      style={{ backgroundColor: color, color: "#0a0a1a" }}
    >
      {strategy}
    </span>
  );
}
