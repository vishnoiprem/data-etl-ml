import { useEffect, useState } from "react";
import Plot from "react-plotly.js";
import { getEvalSummary, getEvalRows, ingestEval, type EvalDetailRow, type EvalSummaryRow } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Button } from "./ui/button";
import { STRATEGIES } from "@/lib/api";
import { RefreshCw } from "lucide-react";

export function EvalDashboard() {
  const [summary, setSummary] = useState<EvalSummaryRow[]>([]);
  const [rows, setRows] = useState<EvalDetailRow[]>([]);
  const [kindFilter, setKindFilter] = useState<string>("two-hop");
  const [strategyFilter, setStrategyFilter] = useState<string>("graph");
  const [loading, setLoading] = useState(false);
  const [ingesting, setIngesting] = useState(false);

  async function load() {
    setLoading(true);
    try {
      const [s, r] = await Promise.all([
        getEvalSummary(),
        getEvalRows(kindFilter, strategyFilter),
      ]);
      setSummary(s.rows);
      setRows(r);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [kindFilter, strategyFilter]);

  async function reingest() {
    setIngesting(true);
    try {
      await ingestEval();
      await load();
    } finally {
      setIngesting(false);
    }
  }

  // Heatmap data
  const kinds = Array.from(new Set(summary.map((r) => r.kind)));
  const heatmapZ: number[][] = [];
  const heatmapText: string[][] = [];
  for (const k of kinds) {
    const row: number[] = [];
    const trow: string[] = [];
    for (const s of STRATEGIES) {
      const m = summary.find((r) => r.kind === k && r.strategy === s);
      const v = m ? Math.round(m.citation_precision * 100) : 0;
      row.push(v);
      trow.push(`${v}%`);
    }
    heatmapZ.push(row);
    heatmapText.push(trow);
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold">Eval dashboard</h2>
        <Button onClick={reingest} disabled={ingesting}>
          <RefreshCw className={`h-4 w-4 mr-2 ${ingesting ? "animate-spin" : ""}`} />
          Re-ingest from API
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Citation precision — strategy × eval set</CardTitle>
        </CardHeader>
        <CardContent>
          {kinds.length === 0 ? (
            <div className="text-muted-foreground text-sm">
              No eval data in ClickHouse yet. Click "Re-ingest from API" to run the eval
              and populate the table.
            </div>
          ) : (
            <Plot
              data={[
                {
                  z: heatmapZ,
                  x: [...STRATEGIES],
                  y: kinds,
                  type: "heatmap",
                  colorscale: "Viridis",
                  zmin: 0,
                  zmax: 100,
                  text: heatmapText,
                  texttemplate: "%{text}",
                  textfont: { size: 14, color: "white" },
                  hovertemplate: "<b>%{y}</b> / <b>%{x}</b><br>precision: %{z}%<extra></extra>",
                },
              ]}
              layout={{
                paper_bgcolor: "transparent",
                plot_bgcolor: "transparent",
                font: { color: "#cbd5e1" },
                margin: { l: 100, r: 20, t: 20, b: 60 },
                height: 280,
                xaxis: { side: "bottom" },
              }}
              useResizeHandler
              style={{ width: "100%", height: "280px" }}
              config={{ displayModeBar: false }}
            />
          )}
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <CardTitle>Summary table</CardTitle>
          </CardHeader>
          <CardContent>
            <table className="w-full text-sm">
              <thead>
                <tr className="text-muted-foreground text-xs">
                  <th className="text-left">Eval set</th>
                  <th className="text-left">Strategy</th>
                  <th className="text-right">n</th>
                  <th className="text-right">Prec.</th>
                  <th className="text-right">KW</th>
                  <th className="text-right">Ref%</th>
                </tr>
              </thead>
              <tbody>
                {summary.map((r, i) => (
                  <tr key={i} className="border-t border-border">
                    <td className="py-1.5">{r.kind}</td>
                    <td className="py-1.5 font-mono text-xs">{r.strategy}</td>
                    <td className="py-1.5 text-right">{r.n}</td>
                    <td className="py-1.5 text-right">{Math.round(r.citation_precision * 100)}%</td>
                    <td className="py-1.5 text-right">{Math.round(r.keyword_hit * 100)}%</td>
                    <td className="py-1.5 text-right">{Math.round(r.refused * 100)}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Drill-down</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex gap-2 mb-3 text-xs">
              <select
                className="rounded bg-muted border border-border px-2 py-1"
                value={kindFilter}
                onChange={(e) => setKindFilter(e.target.value)}
              >
                <option value="single-hop">single-hop</option>
                <option value="two-hop">two-hop</option>
                <option value="adversarial">adversarial</option>
              </select>
              <select
                className="rounded bg-muted border border-border px-2 py-1"
                value={strategyFilter}
                onChange={(e) => setStrategyFilter(e.target.value)}
              >
                {STRATEGIES.map((s) => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
            </div>
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {loading && <div className="text-muted-foreground text-sm">Loading…</div>}
              {rows.map((r, i) => (
                <div key={i} className="rounded border border-border p-2 text-xs space-y-1">
                  <div className="font-medium">{r.question}</div>
                  <div className="text-muted-foreground">
                    cp={Math.round(r.citation_precision * 100)}% · kw={Math.round(r.keyword_hit_rate * 100)}% · refused={String(r.refused)}
                  </div>
                  <div className="text-muted-foreground italic line-clamp-2">{r.answer_excerpt}</div>
                </div>
              ))}
              {!loading && rows.length === 0 && (
                <div className="text-muted-foreground text-sm">No rows for this filter.</div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
