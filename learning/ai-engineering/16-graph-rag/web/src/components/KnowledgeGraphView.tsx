import { useEffect, useRef, useState } from "react";
import cytoscape, { type ElementDefinition } from "cytoscape";
import coseBilkent from "cytoscape-cose-bilkent";
import { getGraph, getGraphStats, type GraphResponse } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";

cytoscape.use(coseBilkent);

const TYPE_COLORS: Record<string, string> = {
  Organization: "#22d3ee",
  Document: "#f43f5e",
  Policy: "#a855f7",
  Process: "#8b5cf6",
  Program: "#6366f1",
  Persona: "#3b82f6",
  Role: "#0ea5e9",
  Step: "#d946ef",
  Activity: "#f97316",
  Task: "#fbbf24",
  Tool: "#10b981",
  Convention: "#ec4899",
  Quantity: "#06b6d4",
  Duration: "#64748b",
  Taxonomy: "#facc15",
};

export function KnowledgeGraphView() {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<cytoscape.Core | null>(null);
  const [graph, setGraph] = useState<GraphResponse | null>(null);
  const [stats, setStats] = useState<any>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const [g, s] = await Promise.all([getGraph(), getGraphStats()]);
        setGraph(g);
        setStats(s);
      } catch (e: any) {
        setErr(e.message);
      }
    })();
  }, []);

  useEffect(() => {
    if (!graph || !containerRef.current) return;

    const elements: ElementDefinition[] = [
      ...graph.nodes.map((n) => ({
        data: {
          id: n.id,
          label: n.id,
          type: n.type,
          color: TYPE_COLORS[n.type] ?? "#9d4edd",
          size: Math.max(15, Math.min(45, 15 + n.degree * 4)),
        },
      })),
      ...graph.edges.map((e) => ({
        data: { id: `${e.source}__${e.rel}__${e.target}`, source: e.source, target: e.target, label: e.rel },
      })),
    ];

    if (cyRef.current) cyRef.current.destroy();

    cyRef.current = cytoscape({
      container: containerRef.current,
      elements,
      style: [
        {
          selector: "node",
          style: {
            "background-color": "data(color)",
            label: "data(label)",
            "font-size": "9px",
            color: "#cbd5e1",
            "text-valign": "bottom",
            "text-halign": "center",
            "text-margin-y": 4,
            width: "data(size)" as any,
            height: "data(size)" as any,
            "border-color": "#1e293b",
            "border-width": 1,
          } as any,
        },
        {
          selector: "edge",
          style: {
            width: 0.8,
            "line-color": "#475569",
            "target-arrow-color": "#475569",
            "target-arrow-shape": "triangle",
            "curve-style": "bezier",
            label: "data(label)",
            "font-size": "7px",
            color: "#94a3b8",
            "text-rotation": "autorotate",
            "text-background-color": "#0f172a",
            "text-background-opacity": 0.6,
            "text-background-padding": 2,
          } as any,
        },
      ],
      layout: {
        name: "cose-bilkent",
        animate: false,
        nodeRepulsion: 8000,
        idealEdgeLength: 80,
      } as any,
    });
  }, [graph]);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Knowledge graph</CardTitle>
      </CardHeader>
      <CardContent>
        {err && <div className="text-destructive text-sm">{err}</div>}
        {!err && stats && (
          <div className="flex gap-4 text-xs text-muted-foreground mb-2">
            <span>{stats.nodes} nodes</span>
            <span>{stats.edges} edges</span>
            <span>{Object.keys(stats.node_types).length} node types</span>
            <span>{Object.keys(stats.rel_types).length} relation types</span>
          </div>
        )}
        <div
          ref={containerRef}
          style={{ width: "100%", height: "640px", background: "#0a0a1a", borderRadius: "0.5rem" }}
        />
      </CardContent>
    </Card>
  );
}
