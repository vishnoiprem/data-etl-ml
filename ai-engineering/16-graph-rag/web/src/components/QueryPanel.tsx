import { useEffect, useState } from "react";
import { ask, type QueryResponse } from "@/lib/api";
import { STRATEGY_COLORS } from "@/lib/utils";
import { StrategyBadge } from "./StrategyBadge";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import { Loader2 } from "lucide-react";

export function QueryPanel({
  question,
  strategy,
  label,
}: {
  question: string;
  strategy: string;
  label?: string;
}) {
  const [data, setData] = useState<QueryResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function run() {
    setLoading(true);
    setErr(null);
    try {
      const r = await ask(question, strategy);
      setData(r);
    } catch (e: any) {
      setErr(e.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (question) run();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [question, strategy]);

  return (
    <Card>
      <CardHeader className="pb-2 flex flex-row items-center justify-between">
        <div className="flex items-center gap-2">
          <StrategyBadge strategy={strategy} />
          {label && <CardTitle className="text-base">{label}</CardTitle>}
        </div>
        <Button size="sm" variant="outline" onClick={run} disabled={loading}>
          {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : "Re-run"}
        </Button>
      </CardHeader>
      <CardContent>
        {err && <div className="text-destructive text-sm">{err}</div>}
        {!data && !err && (
          <div className="text-muted-foreground text-sm italic">Asking…</div>
        )}
        {data && (
          <div className="space-y-3">
            <div className="rounded-md border-l-4 border-primary bg-accent/40 p-3 text-sm">
              {data.answer}
            </div>
            {data.refused && (
              <Badge variant="outline" className="border-destructive text-destructive">
                Refused
              </Badge>
            )}
            <div className="text-xs text-muted-foreground">
              {data.latency_ms} ms · {data.citations.length} citations
            </div>
            {data.citations.length > 0 && (
              <table className="w-full text-xs">
                <thead>
                  <tr className="text-muted-foreground">
                    <th className="text-left font-medium">Source</th>
                    <th className="text-left font-medium">Doc</th>
                    <th className="text-left font-medium">Chunk</th>
                  </tr>
                </thead>
                <tbody>
                  {data.citations.map((c, i) => (
                    <tr key={i} className="border-t border-border">
                      <td className="py-1 pr-2">
                        <span style={{ color: STRATEGY_COLORS[c.source] }}>{c.source}</span>
                      </td>
                      <td className="py-1 pr-2 font-mono">{c.doc_id}</td>
                      <td className="py-1 font-mono text-muted-foreground">{c.chunk_id}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
            {data.graph_edges.length > 0 && (
              <details className="text-xs">
                <summary className="cursor-pointer text-muted-foreground hover:text-foreground">
                  Graph trace ({data.graph_edges.length} edges, {data.graph_seeds.length} seeds)
                </summary>
                <div className="mt-2 space-y-1 font-mono">
                  {data.graph_edges.map(([s, r, t], i) => (
                    <div key={i} className="rounded bg-accent/40 px-2 py-1">
                      {s} <span className="text-primary">--[{r}]--&gt;</span> {t}
                    </div>
                  ))}
                </div>
              </details>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
