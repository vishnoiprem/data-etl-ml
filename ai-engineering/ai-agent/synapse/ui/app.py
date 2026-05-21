"""
Synapse — Daily Intelligence Brief
Streamlit UI that orchestrates Scout → Publisher agents and renders the report.

Run: streamlit run ui/app.py
"""

import asyncio
import sys
from pathlib import Path

import nest_asyncio
import streamlit as st

# Allow asyncio.run() inside an already-running loop (Streamlit compat)
nest_asyncio.apply()

# Project root on sys.path so agent imports resolve
_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_ROOT))

from agents.publisher_agent.agent import PublisherAgent
from agents.scout_agent.agent import ScoutAgent
from protocol.messages import PublishRequest, ScoutRequest, ScoutResponse, Signal

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Synapse · Daily Brief",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ── Helpers ──────────────────────────────────────────────────────────────────
def run_async(coro):
    """Run an async coroutine synchronously (Streamlit-safe)."""
    return asyncio.run(coro)


def _badge(label: str, color: str = "#444") -> str:
    return (
        f'<span style="background:{color};color:#fff;padding:2px 8px;'
        f'border-radius:12px;font-size:0.75rem;font-weight:600">{label}</span>'
    )


def render_news(signal: Signal) -> None:
    articles = signal.data.get("articles", []) if not signal.error else []
    if signal.error:
        st.warning(f"News unavailable: {signal.error}")
    if not articles:
        st.caption("No articles found.")
        return
    for art in articles:
        with st.container():
            source = art.get("source", "")
            pub = art.get("published_at", "")[:10]
            st.markdown(
                f"**[{art.get('title', 'Untitled')}]({art.get('url', '#')})**  \n"
                f"{_badge(source)} {_badge(pub, '#0066cc')}",
                unsafe_allow_html=True,
            )
            if art.get("description"):
                st.caption(art["description"])
            st.divider()


def render_weather(signal: Signal) -> None:
    if signal.error:
        st.warning(f"Weather unavailable: {signal.error}")
        return
    d = signal.data
    if "error" in d:
        st.warning(d["error"])
        return

    col1, col2, col3 = st.columns(3)
    col1.metric("Temperature", f"{d.get('temperature_c', 'N/A')} °C",
                f"Feels like {d.get('feels_like_c', 'N/A')} °C")
    col2.metric("Humidity", f"{d.get('humidity_pct', 'N/A')} %")
    col3.metric("Wind", f"{d.get('wind_speed_ms', 'N/A')} m/s")
    st.caption(f"**{d.get('city', '')}**, {d.get('country', '')} — {d.get('description', '').capitalize()}")


def render_finance(signal: Signal) -> None:
    if signal.error:
        st.warning(f"Finance data unavailable: {signal.error}")
        return

    indices = signal.data.get("indices", [])
    if indices:
        st.markdown("**Major Indices**")
        cols = st.columns(len(indices))
        for col, idx in zip(cols, indices):
            change = idx.get("change_pct")
            delta = f"{change:+.2f}%" if change is not None else None
            col.metric(idx["name"], f"{idx.get('price', 'N/A'):,.2f}" if idx.get("price") else "N/A", delta)

    tickers = signal.data.get("tickers", [])
    if tickers:
        st.markdown("**Related Stocks**")
        cols = st.columns(len(tickers))
        for col, t in zip(cols, tickers):
            change = t.get("change_pct")
            delta = f"{change:+.2f}%" if change is not None else None
            col.metric(t["symbol"], f"${t.get('price', 'N/A')}", delta)


def render_images(signal: Signal) -> None:
    if signal.error:
        st.warning(f"Images unavailable: {signal.error}")
        return
    images = signal.data.get("images", [])
    if not images:
        st.caption("No images found.")
        return

    cols = st.columns(len(images))
    for col, img in zip(cols, images):
        col.image(img["url"], caption=f"📸 {img.get('photographer', '')}", use_container_width=True)


def render_context(scout: ScoutResponse) -> None:
    """Render all signals in expandable sections below the article."""
    st.markdown("---")
    st.subheader("Supporting Context")

    with st.expander("📰 News", expanded=False):
        news = scout.get_signal("news")
        if news:
            render_news(news)

    with st.expander("🌤 Weather", expanded=False):
        weather = scout.get_signal("weather")
        if weather:
            render_weather(weather)

    with st.expander("📈 Markets", expanded=False):
        finance = scout.get_signal("finance")
        if finance:
            render_finance(finance)

    with st.expander("🖼 Images", expanded=False):
        media = scout.get_signal("media")
        if media:
            render_images(media)


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("⚡ Synapse")
    st.caption("AI-powered daily intelligence briefs")
    st.divider()

    topic = st.text_input("Topic", value="Artificial Intelligence", placeholder="e.g. Climate Change")
    city = st.text_input("City", value="San Francisco", placeholder="e.g. London")

    st.divider()
    generate = st.button("Generate Brief", type="primary", use_container_width=True)

    st.divider()
    st.markdown(
        """
**How it works:**
1. 🔍 Scout Agent calls 4 MCP servers
2. 📡 Collects news · weather · finance · images
3. ✍️ Publisher Agent drafts the article with Claude
        """
    )


# ── Main area ─────────────────────────────────────────────────────────────────
st.markdown(
    "<h1 style='font-size:2.5rem;font-weight:800;margin-bottom:0'>Daily Intelligence Brief</h1>",
    unsafe_allow_html=True,
)
st.caption("Enter a topic and city in the sidebar, then click **Generate Brief**.")

if not generate:
    st.info("👈 Fill in the sidebar and click **Generate Brief** to start.")
    st.stop()

if not topic.strip() or not city.strip():
    st.error("Please enter both a topic and a city.")
    st.stop()

# ── Pipeline execution ────────────────────────────────────────────────────────
scout_agent = ScoutAgent()
publisher_agent = PublisherAgent()

with st.status("Generating your daily brief…", expanded=True) as status:
    # Step 1: Scout
    st.write(f"🔍 Scouting data for **{topic}** in **{city}**…")
    try:
        scout_response: ScoutResponse = run_async(
            scout_agent.scout(ScoutRequest(topic=topic, city=city))
        )
        ok_sources = [s.source for s in scout_response.signals if not s.error]
        err_sources = [s.source for s in scout_response.signals if s.error]
        st.write(f"✅ Signals collected: {', '.join(ok_sources)}")
        if err_sources:
            st.write(f"⚠️ Partial errors: {', '.join(err_sources)} (article will proceed)")
    except Exception as exc:
        status.update(label="Scout failed", state="error")
        st.error(f"Scout Agent error: {exc}")
        st.stop()

    # Step 2: Publish
    st.write("✍️ Drafting article with Claude…")
    try:
        publish_response = run_async(
            publisher_agent.publish(PublishRequest(scout_response=scout_response))
        )
        status.update(label="Brief ready!", state="complete", expanded=False)
    except Exception as exc:
        status.update(label="Publishing failed", state="error")
        st.error(f"Publisher Agent error: {exc}")
        st.stop()

# ── Article display ───────────────────────────────────────────────────────────
st.markdown(publish_response.article)

# Token usage badge
meta = publish_response.metadata
st.caption(
    f"Generated by `{meta.get('model', 'claude')}` · "
    f"{meta.get('input_tokens', '?')} in / {meta.get('output_tokens', '?')} out tokens"
)

# ── Context panels ────────────────────────────────────────────────────────────
render_context(scout_response)
