"""Streamlit dashboard for 16-graph-rag.

Run with:
    streamlit run dashboard.py

Five tabs:
    1. Overview          — headline numbers
    2. Money Shot        — two-hop question, side-by-side vector vs hybrid
    3. Try It Yourself   — pick a question, compare all 4 strategies
    4. Knowledge Graph   — interactive plotly network of the extracted graph
    5. Eval Dashboard    — strategy × eval-set table, per-question drill-down
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.config import PROJECT_ROOT, get_settings
from src.ingestion import read_jsonl
from src.pipeline import STRATEGIES, GraphRAGPipeline


# ─────────────────────────────────────────────────────────────────────────────
# Page config + theme
# ─────────────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Graph RAG — 16",
    page_icon="🕸️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS — a touch of polish
st.markdown(
    """
    <style>
    .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
    .metric-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        padding: 1.2rem; border-radius: 0.5rem; color: #fff;
        border-left: 4px solid #4cc9f0;
    }
    .metric-card .label { color: #a0a0b0; font-size: 0.85rem; }
    .metric-card .value { font-size: 1.8rem; font-weight: 700; color: #4cc9f0; }
    .stTabs [data-baseweb="tab-list"] { gap: 1rem; }
    .stTabs [data-baseweb="tab"] {
        padding: 0.6rem 1.2rem; font-weight: 600;
    }
    div[data-testid="stMarkdownContainer"] p { margin-bottom: 0.4rem; }
    .citation {
        background: #1a1a2e; color: #c5c5d5; padding: 0.5rem 0.8rem;
        border-radius: 0.3rem; font-family: monospace; font-size: 0.85rem;
        margin: 0.2rem 0;
    }
    .strategy-tag {
        display: inline-block; padding: 2px 10px; border-radius: 12px;
        font-size: 0.75rem; font-weight: 700; margin-right: 4px;
    }
    .tag-vector  { background: #4cc9f0; color: #0a0a1a; }
    .tag-bm25    { background: #f72585; color: #fff; }
    .tag-graph   { background: #b5179e; color: #fff; }
    .tag-hybrid  { background: #7209b7; color: #fff; }
    </style>
    """,
    unsafe_allow_html=True,
)


# ─────────────────────────────────────────────────────────────────────────────
# Cached loaders
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_resource(show_spinner="Loading pipeline (first run only)…")
def load_pipeline() -> GraphRAGPipeline:
    s = get_settings()
    if not s.graph_path().exists():
        st.error(
            f"No persisted indices found at {s.graph_path()}.  "
            "Run `make ingest` first."
        )
        st.stop()
    p = GraphRAGPipeline()
    p.load()
    return p


@st.cache_data
def load_eval_data() -> dict[str, list[dict]]:
    s = get_settings()
    out: dict[str, list[dict]] = {}
    for name, fname in [
        ("single-hop", "eval_golden.jsonl"),
        ("two-hop", "eval_twohop.jsonl"),
        ("adversarial", "eval_adversarial.jsonl"),
    ]:
        path = s.sample_data_dir / fname
        if path.exists():
            out[name] = read_jsonl(path)
    return out


@st.cache_data
def load_eval_report() -> pd.DataFrame | None:
    s = get_settings()
    path = s.data_dir / "eval_report.jsonl"
    if not path.exists():
        return None
    return pd.DataFrame(read_jsonl(path))


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def strategy_tag(s: str) -> str:
    cls = {
        "vector": "tag-vector",
        "bm25": "tag-bm25",
        "graph": "tag-graph",
        "hybrid": "tag-hybrid",
    }.get(s, "tag-vector")
    return f'<span class="strategy-tag {cls}">{s}</span>'


def metric_card(label: str, value: str) -> str:
    return f'<div class="metric-card"><div class="label">{label}</div><div class="value">{value}</div></div>'


def show_answer(answer, retrieved) -> None:
    st.markdown("**Answer**")
    st.info(answer.text)
    if answer.citations:
        st.markdown("**Citations**")
        rows = [
            {
                "Strategy": c.source,
                "Doc": c.doc_id,
                "Chunk": c.chunk_id,
                "Score": f"{h.score:.3f}",
            }
            for c, h in zip(answer.citations, retrieved.hits)
        ]
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    if retrieved.graph_edges:
        with st.expander(f"🕸️  Graph trace ({len(retrieved.graph_edges)} edges)"):
            st.markdown(f"**Seed entities:** {', '.join(retrieved.graph_seeds) or '(none)'}")
            for s_, r, t in retrieved.graph_edges:
                st.markdown(
                    f'<div class="citation">{s_} &nbsp;<b>--[{r}]-->&nbsp;</b> {t}</div>',
                    unsafe_allow_html=True,
                )


# ─────────────────────────────────────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.title("🕸️ Graph RAG")
    st.caption("Project 16 — ai-engineering portfolio")
    pipeline = load_pipeline()
    st.success(f"Pipeline loaded — {len(pipeline.chunks)} chunks, {len(pipeline.graph)} graph nodes")
    st.divider()
    st.markdown("**Run anywhere**")
    st.code("streamlit run dashboard.py", language="bash")
    st.markdown("**Rebuild**")
    st.code("make ingest", language="bash")
    st.markdown("**Eval**")
    st.code("make eval", language="bash")
    st.divider()
    st.caption("Mock LLM by default. Set `ANTHROPIC_API_KEY` and `LLM_MODE=real` to use Claude.")


# ─────────────────────────────────────────────────────────────────────────────
# Tabs
# ─────────────────────────────────────────────────────────────────────────────

tab_overview, tab_money, tab_try, tab_graph, tab_eval = st.tabs(
    ["📊 Overview", "🎯 Money Shot", "🔍 Try It Yourself", "🕸️ Knowledge Graph", "📈 Eval Dashboard"]
)

# ── Tab 1: Overview ─────────────────────────────────────────────────────────

with tab_overview:
    st.header("Project 16 — Graph RAG")
    st.markdown(
        """
        **Hybrid retrieval** combining **vector search** (FAISS), **lexical search** (BM25),
        and a **knowledge graph** (NetworkX + SQLite) — fused with **Reciprocal Rank Fusion**.

        The graph is built by extracting `(entity, relation, entity)` triples from each
        chunk using the LLM, then querying it as a separate retrieval path.
        """
    )

    # Headline metric cards
    cols = st.columns(5)
    n_chunks = len(pipeline.chunks)
    n_docs = len({c.doc_id for c in pipeline.chunks})
    n_nodes = len(pipeline.graph)
    n_edges = len(pipeline.graph.edges())
    eval_df = load_eval_report()
    two_hop_graph = (
        eval_df[(eval_df["kind"] == "two-hop") & (eval_df["strategy"] == "graph")]["citation_precision"].mean()
        if eval_df is not None
        else 0
    )
    two_hop_vector = (
        eval_df[(eval_df["kind"] == "two-hop") & (eval_df["strategy"] == "vector")]["citation_precision"].mean()
        if eval_df is not None
        else 0
    )

    with cols[0]:
        st.markdown(metric_card("Documents", str(n_docs)), unsafe_allow_html=True)
    with cols[1]:
        st.markdown(metric_card("Chunks", str(n_chunks)), unsafe_allow_html=True)
    with cols[2]:
        st.markdown(metric_card("Graph nodes", str(n_nodes)), unsafe_allow_html=True)
    with cols[3]:
        st.markdown(metric_card("Graph edges", str(n_edges)), unsafe_allow_html=True)
    with cols[4]:
        if eval_df is not None and not eval_df.empty:
            delta = (two_hop_graph - two_hop_vector) * 100
            st.markdown(
                metric_card("Graph edge on 2-hop", f"+{delta:.0f} pp"),
                unsafe_allow_html=True,
            )
        else:
            st.markdown(metric_card("Graph edge on 2-hop", "—"), unsafe_allow_html=True)

    st.divider()

    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("Architecture")
        st.code(
            """
            user question
                  │
                  ▼
          ┌─ Entity linker (substring)
          │
          ├─► Vector (FAISS)      ──┐
          ├─► BM25                 ─┼─► RRF fusion ─► Claude ─► answer
          └─► Graph (NetworkX)    ──┘
            """,
            language="text",
        )
    with col_b:
        st.subheader("Why it works")
        st.markdown(
            """
            - **Vector** — semantic similarity (good for "find me docs about X")
            - **BM25** — exact keyword match (good for "VP", "SEV1", proper nouns)
            - **Graph** — entity relations (good for "what's the path A→B→C?")
            - **Hybrid (RRF)** — rank-based fusion, no score normalisation needed

            See [`README.md`](https://github.com) for the full design rationale.
            """,
        )

    if eval_df is not None and not eval_df.empty:
        st.divider()
        st.subheader("Eval snapshot")
        snap = (
            eval_df.groupby(["kind", "strategy"])
            .agg(
                n=("question", "count"),
                citation_precision=("citation_precision", "mean"),
                keyword_hit=("keyword_hit_rate", "mean"),
                refused=("refused", "mean"),
            )
            .reset_index()
        )
        snap["citation_precision"] = (snap["citation_precision"] * 100).round(0).astype(int)
        snap["keyword_hit"] = (snap["keyword_hit"] * 100).round(0).astype(int)
        snap["refused"] = (snap["refused"] * 100).round(0).astype(int)
        snap = snap.rename(
            columns={
                "kind": "Eval set",
                "strategy": "Strategy",
                "n": "n",
                "citation_precision": "Citation prec. %",
                "keyword_hit": "Keyword hit %",
                "refused": "Refused %",
            }
        )
        st.dataframe(snap, use_container_width=True, hide_index=True)


# ── Tab 2: Money Shot ───────────────────────────────────────────────────────

with tab_money:
    st.header("🎯 The Two-Hop Money Shot")
    st.markdown(
        """
        > *"I'm a new hire about to travel internationally for a client visit. What is the approval path?"*

        This question requires facts from `onboarding.md`, `it-runbooks.md`, **and**
        `expense-policy.md`. No single document has the full answer.
        """
    )

    money_q = "I'm a new hire about to travel internationally for a client visit. What is the approval path?"

    if st.button("🚀 Run money shot", type="primary"):
        with st.spinner("Querying all 4 strategies…"):
            st.session_state["money_results"] = {
                s: pipeline.query(money_q, strategy=s) for s in STRATEGIES
            }
            st.session_state["money_retrieved"] = {
                s: pipeline.retrieve(money_q, strategy=s) for s in STRATEGIES
            }

    if "money_results" in st.session_state:
        results = st.session_state["money_results"]
        retrieved = st.session_state["money_retrieved"]

        # Top row: vector vs hybrid
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Vector-only (the old way)")
            st.caption("Returns the closest single doc; misses the chain")
            show_answer(results["vector"], retrieved["vector"])
        with c2:
            st.subheader("Hybrid (vector + BM25 + graph)")
            st.caption("Fuses all three; surfaces the relation chain")
            show_answer(results["hybrid"], retrieved["hybrid"])

        st.divider()
        st.subheader("All four strategies, side by side")
        for strat in ["bm25", "graph"]:
            with st.expander(f"{strat.upper()} — click to expand", expanded=(strat == "graph")):
                show_answer(results[strat], retrieved[strat])


# ── Tab 3: Try It Yourself ──────────────────────────────────────────────────

with tab_try:
    st.header("🔍 Try It Yourself")
    st.caption("Pick a question from the eval set, or write your own. All four strategies run in parallel.")

    eval_data = load_eval_data()
    canned_questions: list[tuple[str, str]] = []
    for kind, rows in eval_data.items():
        for r in rows:
            canned_questions.append((f"[{kind}] {r['question']}", r["question"]))

    col_q, col_btn = st.columns([4, 1])
    with col_q:
        choice = st.selectbox(
            "Sample question",
            options=["(custom)"] + [label for label, _ in canned_questions],
            index=0,
        )
    question = st.text_input(
        "Your question",
        value=next((q for label, q in canned_questions if label == choice), money_q if "money_q" in dir() else ""),
    )

    if st.button("Ask", type="primary") and question.strip():
        with st.spinner("Querying all 4 strategies…"):
            results = {s: pipeline.query(question, strategy=s) for s in STRATEGIES}
            retrieved = {s: pipeline.retrieve(question, strategy=s) for s in STRATEGIES}

        # 2x2 grid
        c1, c2 = st.columns(2)
        c3, c4 = st.columns(2)
        for col, strat in zip([c1, c2, c3, c4], STRATEGIES):
            with col:
                st.markdown(strategy_tag(strat), unsafe_allow_html=True)
                show_answer(results[strat], retrieved[strat])


# ── Tab 4: Knowledge Graph ──────────────────────────────────────────────────

with tab_graph:
    st.header("🕸️ Knowledge Graph")
    st.caption(
        f"Built by the LLM extracting `(entity, relation, entity)` triples from each chunk. "
        f"{len(pipeline.graph)} nodes, {len(pipeline.graph.edges())} edges."
    )

    g = pipeline.graph._g  # noqa: SLF001  — internal but read-only here
    # Build a plotly network: nodes positioned via a quick spring layout
    try:
        from networkx.drawing.spring_layout import spring_layout  # type: ignore

        pos = spring_layout(g, seed=42, k=1.5 / max(1, len(g.nodes) ** 0.5))
    except Exception:
        pos = {n: (i, 0) for i, n in enumerate(g.nodes)}

    # Color nodes by type
    node_types: dict[str, str] = {n: g.nodes[n].get("type", "Thing") for n in g.nodes}
    type_color = {
        "Organization": "#4cc9f0",
        "Document": "#f72585",
        "Policy": "#b5179e",
        "Process": "#7209b7",
        "Program": "#3a0ca3",
        "Persona": "#4361ee",
        "Role": "#4895ef",
        "Step": "#560bad",
        "Activity": "#f77f00",
        "Task": "#fcbf49",
        "Tool": "#06d6a0",
        "Convention": "#ef476f",
        "Quantity": "#118ab2",
        "Duration": "#073b4c",
        "Taxonomy": "#ffd166",
    }
    default_color = "#9d4edd"
    node_colors = [type_color.get(node_types[n], default_color) for n in g.nodes]
    node_x = [pos[n][0] for n in g.nodes]
    node_y = [pos[n][1] for n in g.nodes]
    node_text = [f"{n}<br>type: {node_types[n]}" for n in g.nodes]
    node_sizes = [max(12, min(40, 12 + g.degree(n) * 3)) for n in g.nodes]

    edge_x: list[float] = []
    edge_y: list[float] = []
    edge_text: list[str] = []
    for u, v, k, d in g.edges(keys=True, data=True):
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        edge_x += [x0, x1, None]
        edge_y += [y0, y1, None]
        edge_text.append(d.get("rel", k))

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=edge_x,
            y=edge_y,
            line=dict(width=0.6, color="#555"),
            hoverinfo="none",
            mode="lines",
            showlegend=False,
        )
    )
    fig.add_trace(
        go.Scatter(
            x=node_x,
            y=node_y,
            mode="markers+text",
            marker=dict(size=node_sizes, color=node_colors, line=dict(width=1, color="#fff")),
            text=[n for n in g.nodes],
            textposition="top center",
            textfont=dict(size=9, color="#ddd"),
            hovertext=node_text,
            hoverinfo="text",
            showlegend=False,
        )
    )
    fig.update_layout(
        title=f"AcmeCorp Knowledge Graph ({len(g.nodes)} nodes, {g.number_of_edges()} edges)",
        showlegend=False,
        hovermode="closest",
        margin=dict(b=20, l=5, r=5, t=40),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        plot_bgcolor="#0a0a1a",
        paper_bgcolor="#0a0a1a",
        font=dict(color="#ddd"),
        height=620,
    )
    st.plotly_chart(fig, use_container_width=True)

    # Edge list (sortable)
    with st.expander("📋 Full edge list"):
        edges_df = pd.DataFrame(
            [
                {"head": u, "relation": d.get("rel", k), "tail": v}
                for u, v, k, d in g.edges(keys=True, data=True)
            ]
        )
        st.dataframe(edges_df, use_container_width=True, hide_index=True)

    # Node type legend
    st.markdown("**Node types**")
    legend_cols = st.columns(min(5, len(set(node_types.values()))))
    used = sorted(set(node_types.values()))
    for i, t in enumerate(used):
        with legend_cols[i % len(legend_cols)]:
            color = type_color.get(t, default_color)
            st.markdown(
                f'<span style="display:inline-block;width:10px;height:10px;'
                f'background:{color};border-radius:50%;margin-right:6px;"></span>{t}',
                unsafe_allow_html=True,
            )


# ── Tab 5: Eval Dashboard ───────────────────────────────────────────────────

with tab_eval:
    st.header("📈 Eval Dashboard")
    eval_df = load_eval_report()

    if eval_df is None or eval_df.empty:
        st.warning("No eval report found. Run `make eval` to generate one.")
        if st.button("▶ Run eval now"):
            with st.spinner("Running eval (this can take ~30s)…"):
                import subprocess

                subprocess.run(
                    ["python3", "scripts/evaluate.py"],
                    cwd=str(PROJECT_ROOT),
                    check=False,
                )
            st.rerun()
    else:
        # Heatmap: strategy × eval-set, citation precision
        st.subheader("Citation precision — strategy × eval set")
        heat = (
            eval_df.groupby(["kind", "strategy"])["citation_precision"]
            .mean()
            .mul(100)
            .round(0)
            .reset_index()
        )
        pivot = heat.pivot(index="kind", columns="strategy", values="citation_precision").fillna(0)
        # Reorder columns
        pivot = pivot[[c for c in STRATEGIES if c in pivot.columns]]
        fig = px.imshow(
            pivot,
            text_auto=True,
            color_continuous_scale="Viridis",
            aspect="auto",
            zmin=0,
            zmax=100,
        )
        fig.update_layout(
            plot_bgcolor="#0a0a1a",
            paper_bgcolor="#0a0a1a",
            font=dict(color="#ddd"),
            height=320,
            margin=dict(l=80, r=20, t=20, b=20),
        )
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("All metrics")
        summary = (
            eval_df.groupby(["kind", "strategy"])
            .agg(
                n=("question", "count"),
                citation_precision=("citation_precision", "mean"),
                keyword_hit=("keyword_hit_rate", "mean"),
                refused=("refused", "mean"),
            )
            .reset_index()
        )
        summary["citation_precision"] = (summary["citation_precision"] * 100).round(0).astype(int)
        summary["keyword_hit"] = (summary["keyword_hit"] * 100).round(0).astype(int)
        summary["refused"] = (summary["refused"] * 100).round(0).astype(int)
        summary = summary.rename(
            columns={
                "kind": "Eval set",
                "strategy": "Strategy",
                "n": "n",
                "citation_precision": "Citation prec. %",
                "keyword_hit": "Keyword hit %",
                "refused": "Refused %",
            }
        )
        st.dataframe(summary, use_container_width=True, hide_index=True)

        st.divider()
        st.subheader("Per-question drill-down")
        eval_set = st.selectbox("Eval set", options=sorted(eval_df["kind"].unique()))
        strategy = st.selectbox("Strategy", options=list(STRATEGIES))
        sub = eval_df[(eval_df["kind"] == eval_set) & (eval_df["strategy"] == strategy)]
        for _, row in sub.iterrows():
            with st.expander(
                f"Q: {row['question'][:100]}{'…' if len(row['question']) > 100 else ''}  •  cp={row['citation_precision']:.0%}  •  kh={row['keyword_hit_rate']:.0%}  •  refused={row['refused']}"
            ):
                st.markdown(f"**Question:** {row['question']}")
                st.markdown(f"**Cited docs:** {', '.join(row['cited_doc_ids']) or '(none)'}")
                st.markdown(f"**Expected docs:** {', '.join(row['expected_doc_ids']) or '(none)'}")
                st.markdown(f"**Answer excerpt:** _{row['answer_excerpt']}_")
