import { useState } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { QueryPanel } from "@/components/QueryPanel";
import { KnowledgeGraphView } from "@/components/KnowledgeGraphView";
import { EvalDashboard } from "@/components/EvalDashboard";
import { STRATEGIES } from "@/lib/api";

const MONEY_QUESTION =
  "I'm a new hire about to travel internationally for a client visit. What is the approval path?";

export default function App() {
  const [customQuestion, setCustomQuestion] = useState(MONEY_QUESTION);

  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="border-b border-border bg-card/40 backdrop-blur sticky top-0 z-10">
        <div className="container mx-auto max-w-7xl flex items-center justify-between py-3">
          <div className="flex items-center gap-2">
            <span className="text-2xl">🕸️</span>
            <h1 className="text-lg font-semibold">Graph RAG</h1>
            <span className="text-xs text-muted-foreground">project 16 · ai-engineering</span>
          </div>
          <div className="text-xs text-muted-foreground">
            React + FastAPI + ClickHouse
          </div>
        </div>
      </header>

      <main className="container mx-auto max-w-7xl py-6">
        <Tabs defaultValue="overview" className="w-full">
          <TabsList className="grid w-full grid-cols-5">
            <TabsTrigger value="overview">📊 Overview</TabsTrigger>
            <TabsTrigger value="money">🎯 Money shot</TabsTrigger>
            <TabsTrigger value="try">🔍 Try it</TabsTrigger>
            <TabsTrigger value="graph">🕸️ Graph</TabsTrigger>
            <TabsTrigger value="eval">📈 Eval</TabsTrigger>
          </TabsList>

          {/* ── Overview ─────────────────────────────────────────────── */}
          <TabsContent value="overview">
            <Card>
              <CardHeader>
                <CardTitle>What is this?</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 text-sm">
                <p>
                  Hybrid retrieval combining <b>vector search</b> (FAISS), <b>lexical search</b>{" "}
                  (BM25), and a <b>knowledge graph</b> (NetworkX + SQLite), fused with{" "}
                  <b>Reciprocal Rank Fusion</b>. The graph is built by extracting
                  <code className="bg-muted px-1 mx-0.5 rounded">(entity, relation, entity)</code>
                  triples from each chunk via the LLM.
                </p>
                <p>
                  The whole stack — <b>React</b> (this UI), <b>FastAPI</b> (the API), and{" "}
                  <b>ClickHouse</b> (the database) — runs via{" "}
                  <code className="bg-muted px-1 rounded">docker compose up</code>.
                </p>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-2 pt-2">
                  {STRATEGIES.map((s) => (
                    <div
                      key={s}
                      className="rounded border border-border p-3 bg-accent/30"
                    >
                      <div className="text-xs uppercase text-muted-foreground">strategy</div>
                      <div className="text-lg font-semibold font-mono">{s}</div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* ── Money Shot ───────────────────────────────────────────── */}
          <TabsContent value="money">
            <div className="space-y-3">
              <Card>
                <CardHeader>
                  <CardTitle>The two-hop question</CardTitle>
                </CardHeader>
                <CardContent>
                  <blockquote className="border-l-4 border-primary pl-4 italic text-muted-foreground">
                    "{MONEY_QUESTION}"
                  </blockquote>
                  <p className="text-sm text-muted-foreground mt-2">
                    Requires facts from <code>onboarding.md</code>,{" "}
                    <code>it-runbooks.md</code>, and <code>expense-policy.md</code>. No single doc
                    has the full answer — graph retrieval should surface the chain.
                  </p>
                </CardContent>
              </Card>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <QueryPanel
                  question={MONEY_QUESTION}
                  strategy="vector"
                  label="Vector-only (old way)"
                />
                <QueryPanel
                  question={MONEY_QUESTION}
                  strategy="hybrid"
                  label="Hybrid (vector + BM25 + graph)"
                />
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <QueryPanel question={MONEY_QUESTION} strategy="bm25" />
                <QueryPanel question={MONEY_QUESTION} strategy="graph" />
              </div>
            </div>
          </TabsContent>

          {/* ── Try It Yourself ──────────────────────────────────────── */}
          <TabsContent value="try">
            <Card>
              <CardHeader>
                <CardTitle>Ask anything</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <textarea
                  className="w-full rounded bg-muted border border-border p-2 text-sm"
                  rows={3}
                  value={customQuestion}
                  onChange={(e) => setCustomQuestion(e.target.value)}
                />
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {STRATEGIES.map((s) => (
                    <QueryPanel key={s} question={customQuestion} strategy={s} />
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* ── Graph ────────────────────────────────────────────────── */}
          <TabsContent value="graph">
            <KnowledgeGraphView />
          </TabsContent>

          {/* ── Eval ─────────────────────────────────────────────────── */}
          <TabsContent value="eval">
            <EvalDashboard />
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
}
