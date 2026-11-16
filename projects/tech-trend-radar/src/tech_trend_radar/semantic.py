"""Semantic topic matching, using local open-weights embeddings.

The lexical extractor in `topics.py` finds topics it already knows: a
curated vocabulary, recurring capitalised phrases, and platform tags. It
misses anything new. A post about a runtime released last week, named in
a way the extractor cannot parse, contributes nothing — and if enough
posts are like that, a real trend stays invisible.

This module adds a fourth signal: a post title is embedded with a local
sentence-transformer and matched against the known technologies. A title
about an unfamiliar technology still lands near its nearest known
neighbour, so it contributes a mention to a topic the radar already
tracks.

**The descriptors matter more than the model.** Embedding the bare word
"rust" gives a vector near every English sentence that uses the word
"rust". Embedding "the Rust systems programming language" gives a vector
near other programming languages. So each vocabulary entry carries a
short descriptor, and it is the descriptor that gets embedded.

**The threshold is deliberately high.** A title that is not about
technology at all — a post about breakfast — still has a nearest
neighbour, and it will score something like 0.11. A title that is about
a technology the vocabulary happens to miss scores 0.4-0.6. The
threshold sits between the two, so the signal has to be strong to count.

**The signal only fires where the lexical path found nothing.** A post
the extractor already resolved keeps its own topics. This is not
cosmetic: a post that mentions `docker` must not *also* count as a
mention of `kubernetes` just because the two are adjacent to an
embedding, because that inflates `kubernetes`'s count in both windows
and flattens the very acceleration the radar measures. Measured on the
burst fixture, the rule is the difference between a burst-detection
accuracy of 0.75 and 1.0.

**The layer degrades.** If `sentence-transformers` is not installed, or
the model weights cannot be loaded, the matcher reports itself
unavailable and the radar runs on the lexical extractor alone. A missing
embedding model must never stop a ranking run.
"""

from __future__ import annotations

import math
import os
from dataclasses import dataclass, field
from typing import Protocol

from .config import (
    SEMANTIC_MAX_MATCHES,
    SEMANTIC_MODEL_NAME,
    SEMANTIC_THRESHOLD,
    Settings,
)

#: The embedding model. Small, fast on CPU, and widely used — the same
#: one the sibling projects in this repo use, so it is usually already
#: in the model cache.
DEFAULT_MODEL_NAME = SEMANTIC_MODEL_NAME

#: How similar a title must be to a technology's descriptor before it
#: counts as a mention of it.
#:
#: Measured on a probe set: titles genuinely about a technology the
#: vocabulary misses scored 0.40-0.63 against their nearest
#: neighbour; titles about nothing technical scored 0.10-0.11. The
#: threshold sits in the gap, with margin on both sides.
DEFAULT_SIMILARITY_THRESHOLD = SEMANTIC_THRESHOLD

#: How many technologies one title may contribute to. A title that
#: matches five technologies is not about five technologies, it is
#: matching nothing in particular — and the signal is noise.
MAX_MATCHES_PER_TITLE = SEMANTIC_MAX_MATCHES

#: The environment variable that turns the layer off.
DISABLE_ENV_VAR = "TREND_RADAR_NO_SEMANTIC"


class Embedder(Protocol):
    """The bit of `sentence-transformers` this module needs."""

    def encode(self, texts: list[str], **kwargs) -> object:
        """Encode texts into a matrix of normalised vectors."""
        ...


@dataclass(slots=True)
class SemanticMatch:
    """One technology a title was matched to, and how strongly."""

    topic: str
    score: float
    surface: str = ""


@dataclass(slots=True)
class SemanticResult:
    """What the semantic layer found for one title."""

    matches: list[SemanticMatch] = field(default_factory=list)
    #: False when the layer could not run — the model is unavailable, or
    #: the layer was switched off. The radar still works; it is just
    #: working with fewer signals.
    enabled: bool = True


#: A short descriptor for each vocabulary entry. Without one, the bare
#: word is embedded, and a word like "rust" or "go" is then close to
#: every sentence that happens to use it.
#:
#: Only entries listed here can be matched semantically. A vocabulary
#: word with no descriptor is matched by exact string only.
TOPIC_DESCRIPTORS: dict[str, str] = {
    "rust": "the Rust systems programming language",
    "go": "the Go programming language by Google",
    "python": "the Python programming language",
    "typescript": "the TypeScript programming language",
    "javascript": "the JavaScript programming language",
    "llm": "large language models and generative artificial intelligence",
    "llms": "large language models and generative artificial intelligence",
    "postgres": "the PostgreSQL relational database",
    "mysql": "the MySQL relational database",
    "sqlite": "the SQLite embedded relational database",
    "kubernetes": "container orchestration with Kubernetes",
    "docker": "Docker container images and containers",
    "react": "the React JavaScript user interface library",
    "vue": "the Vue JavaScript user interface framework",
    "angular": "the Angular web application framework",
    "nodejs": "the Node.js JavaScript runtime",
    "nextjs": "the Next.js React web framework",
    "nuxt": "the Nuxt Vue web framework",
    "svelte": "the Svelte JavaScript user interface framework",
    "pytorch": "the PyTorch deep learning framework",
    "tensorflow": "the TensorFlow machine learning framework",
    "numpy": "the NumPy numerical computing library",
    "pandas": "the pandas data analysis library",
    "spark": "the Apache Spark distributed data processing engine",
    "kafka": "the Apache Kafka event streaming platform",
    "airflow": "the Apache Airflow workflow orchestration platform",
    "dbt": "dbt data transformation and ELT tooling",
    "clickhouse": "the ClickHouse analytical database",
    "duckdb": "the DuckDB embedded analytical database",
    "databricks": "the Databricks data and AI platform",
    "snowflake": "the Snowflake cloud data warehouse",
    "bigquery": "the Google BigQuery cloud data warehouse",
    "flink": "the Apache Flink stream processing framework",
    "elasticsearch": "the Elasticsearch search engine",
    "kibana": "the Kibana visualization tool for Elasticsearch",
    "openai": "OpenAI and its GPT models",
    "chatgpt": "OpenAI ChatGPT the chatbot",
    "claude": "the Claude AI model by Anthropic",
    "anthropic": "Anthropic the AI company",
    "gemini": "the Gemini model by Google",
    "gemma": "the Gemma open weight model by Google",
    "llama": "the Llama open weight model by Meta",
    "mistral": "the Mistral AI open weight models",
    "deepseek": "the DeepSeek AI models",
    "ollama": "running large language models locally with Ollama",
    "vllm": "the vLLM inference server for large language models",
    "copilot": "GitHub Copilot the AI coding assistant",
    "cursor": "the Cursor AI code editor",
    "mcp": "the Model Context Protocol for connecting AI agents to tools",
    "langgraph": "the LangGraph agent orchestration framework",
    "nvidia": "NVIDIA the GPU company and its graphics processors",
    "amd": "AMD the CPU and GPU company and its processors",
    "apple": "Apple the company and its devices",
    "google": "Google the search and cloud company",
    "microsoft": "Microsoft the software company",
    "amazon": "Amazon the ecommerce and cloud company",
    "meta": "Meta the social media company",
    "aws": "Amazon Web Services the cloud platform",
    "gcp": "Google Cloud Platform the cloud platform",
    "azure": "Microsoft Azure the cloud platform",
    "fastapi": "the FastAPI Python web API framework",
    "django": "the Django Python web framework",
    "flask": "the Flask Python micro web framework",
    "rails": "the Ruby on Rails web framework",
    "tailwind": "Tailwind CSS utility first styling",
    "css": "CSS the styling language of the web",
    "html": "HTML the markup language of the web",
    "git": "the Git version control system",
    "github": "the GitHub code hosting platform",
    "gitlab": "the GitLab code hosting platform",
    "linux": "the Linux operating system kernel",
    "windows": "the Microsoft Windows operating system",
    "vim": "the Vim text editor",
    "neovim": "the Neovim text editor",
    "emacs": "the Emacs text editor",
    "vscode": "Visual Studio Code the code editor",
    "wasm": "WebAssembly the portable bytecode format",
    "deno": "the Deno JavaScript and TypeScript runtime",
    "bun": "the Bun JavaScript runtime and package manager",
    "ansible": "Ansible configuration management and automation",
    "terraform": "Terraform infrastructure as code",
    "nginx": "the Nginx web server and reverse proxy",
    "apache": "the Apache open source software foundation projects",
    "huggingface": "the Hugging Face model hub and transformers library",
}


class SemanticMatcher:
    """Matches titles to known technologies by embedding similarity.

    The matcher holds one embedding model and one embedding per
    descriptor. Constructing it loads the model, which is the expensive
    part — so it is built once per run and reused across every title.
    """

    def __init__(
        self,
        embedder: Embedder | None = None,
        model_name: str = DEFAULT_MODEL_NAME,
        threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
        max_matches: int = MAX_MATCHES_PER_TITLE,
    ) -> None:
        self.threshold = threshold
        self.max_matches = max_matches
        self.model_name = model_name
        self._embedder = embedder
        self._descriptor_vectors: object = None
        self._descriptor_topics: list[str] = []
        self._available = False
        self._reason = ""

        if os.environ.get(DISABLE_ENV_VAR):
            self._reason = f"disabled by {DISABLE_ENV_VAR}"
            return

        if self._embedder is None:
            self._embedder = self._load_model(model_name)

        if self._embedder is None:
            self._reason = f"embedding model {model_name} unavailable"
            return

        if not self._index_descriptors():
            # A failed descriptor encode means the layer cannot run. It
            # must not take the radar down with it — the lexical signals
            # are enough to produce a ranking.
            self._reason = f"embedding model {model_name} failed to encode descriptors"
            return

        self._available = True

    # -- construction ---------------------------------------------------

    @staticmethod
    def _load_model(model_name: str = DEFAULT_MODEL_NAME) -> Embedder | None:
        """Load the embedding model, or return None if it is unavailable."""
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            return None
        try:
            return SentenceTransformer(model_name)
        except Exception:  # noqa: BLE001 - any failure means "unavailable"
            return None

    def _index_descriptors(self) -> bool:
        """Embed every descriptor once, up front.

        Returns False when the encode failed, in which case the layer
        reports itself unavailable rather than raising.
        """
        topics: list[str] = []
        descriptors: list[str] = []
        for topic, descriptor in TOPIC_DESCRIPTORS.items():
            if topic in topics:
                continue
            topics.append(topic)
            descriptors.append(descriptor)

        if not descriptors:
            return False

        try:
            vectors = self._embedder.encode(  # type: ignore[union-attr]
                descriptors, normalize_embeddings=True, show_progress_bar=False
            )
        except Exception:  # noqa: BLE001 - a failed encode means "unavailable"
            return False

        self._descriptor_vectors = vectors
        self._descriptor_topics = topics
        return True

    # -- public API -----------------------------------------------------

    @property
    def available(self) -> bool:
        """Whether the semantic layer can run."""
        return self._available

    @property
    def reason(self) -> str:
        """Why the layer is unavailable, when it is."""
        return self._reason

    def _scores_for(self, vector) -> list[float]:
        """The similarity of one embedded text to every descriptor.

        The descriptors are embedded with `normalize_embeddings=True`, so
        the dot product *is* the cosine similarity. The arithmetic is done
        in plain Python rather than with a matrix product, so the layer
        works with any embedder that returns a sequence of floats — not
        only one that returns a numpy array.
        """
        try:
            return [
                sum(float(a) * float(b) for a, b in zip(row, vector, strict=True))
                for row in self._descriptor_vectors  # type: ignore[union-attr]
            ]
        except (TypeError, ValueError):
            return []

    def _matches_for(self, vector) -> list[SemanticMatch]:
        """The topics one embedded text matches, best first."""
        scores = self._scores_for(vector)
        if not scores:
            return []

        order = sorted(range(len(scores)), key=lambda i: -float(scores[i]))
        matches: list[SemanticMatch] = []
        for index in order:
            score = float(scores[index])
            if score < self.threshold:
                break
            matches.append(
                SemanticMatch(topic=self._descriptor_topics[index], score=round(score, 4))
            )
            if len(matches) >= self.max_matches:
                break
        return matches

    def match(self, title: str, description: str = "") -> SemanticResult:
        """The technologies this title is about.

        Returns an empty result — rather than raising — when the layer is
        unavailable, so a caller never has to check first.
        """
        if not self._available or self._descriptor_vectors is None:
            return SemanticResult(matches=[], enabled=False)
        if not title.strip():
            return SemanticResult(matches=[], enabled=True)

        text = title if not description else f"{title}. {description}"
        try:
            vectors = self._embedder.encode(  # type: ignore[union-attr]
                [text], normalize_embeddings=True, show_progress_bar=False
            )
        except Exception:  # noqa: BLE001 - a failed encode must not stop the run
            return SemanticResult(matches=[], enabled=False)

        return SemanticResult(matches=self._matches_for(vectors[0]), enabled=True)

    def match_many(self, titles: list[str]) -> list[SemanticResult]:
        """Match many titles in one batch — one model call, not N."""
        if not self._available or self._descriptor_vectors is None:
            return [SemanticResult(matches=[], enabled=False) for _ in titles]
        if not titles:
            return []

        try:
            vectors = self._embedder.encode(  # type: ignore[union-attr]
                titles, normalize_embeddings=True, show_progress_bar=False
            )
        except Exception:  # noqa: BLE001
            return [SemanticResult(matches=[], enabled=False) for _ in titles]

        return [
            SemanticResult(matches=self._matches_for(vector), enabled=True)
            for vector in vectors
        ]


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Cosine similarity of two vectors — used by the tests."""
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def build_matcher(settings: Settings | None = None) -> SemanticMatcher | None:
    """The matcher for these settings, or None when it cannot be built.

    Returning None rather than an unavailable matcher keeps the call sites
    simple: `if matcher is not None` is the same as "the semantic signal
    is available", and there is no half-built object to check.

    This never raises. A missing `sentence-transformers`, a missing model
    download, a broken weights file — all of them end here, and the radar
    runs on the lexical signals alone.
    """
    settings = settings or Settings()
    if not settings.semantic_enabled:
        return None
    if os.environ.get(DISABLE_ENV_VAR):
        return None

    matcher = SemanticMatcher(
        model_name=settings.semantic_model,
        threshold=settings.semantic_threshold,
        max_matches=settings.semantic_max_matches,
    )
    return matcher if matcher.available else None
