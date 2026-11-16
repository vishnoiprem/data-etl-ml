"""Turning posts into topics.

This is the part of the radar that decides what is being talked *about*. It
is deliberately conservative: a topic has to be a recognisable technology
name, not merely a word that appears often.

Four signals are combined, and a term is only a topic if it earns its place:

1. **A curated technology vocabulary.** `rust`, `kubernetes`, `postgres`,
   `llm` and friends are known technologies. These are recognised outright.
2. **A structural n-gram.** An unknown capitalised phrase — "MCP server",
   "Go 1.24" — is a topic when it recurs across posts. Recurrence is what
   distinguishes a technology from an incidental capitalised word.
3. **Tags.** Platforms hand out tags; a tag that appears on several posts
   is a topic by definition.
4. **A semantic match.** A post about a technology the vocabulary has
   never heard of still lands near its nearest known neighbour, and
   contributes a mention to it. This is the one signal that needs a model,
   so it is the one that is allowed to fail — see `semantic.py`.

The stopword list matters more than any of them. Without it, "how" and
"best" outrank "rust" every time.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .semantic import SemanticMatcher

#: Words that describe how a post is written rather than what it is about.
#: These are the words that dominate tech headlines without naming a single
#: technology.
STOPWORDS: frozenset[str] = frozenset(
    """
    a about above after again against all also am an and any are as at
    be because been before being below between both but by
    can cannot could
    did do does doing done down during
    each even ever every everything
    few for from further
    get gets getting give go goes going got
    had has have having he her here hers herself him himself his how
    i if in into is it its itself
    just keep keeps kept
    let like likely
    make makes making many may maybe me might more most much must my myself
    need needs never new no not now
    of off on once one only or other others ought our ours ourselves out over own
    people per perhaps
    same say says see seem seems should so some something still such
    than that the their theirs them themselves then there these they this those though through to too
    under until up upon us use used uses using usually
    very
    want wants was way we well were what when where whether which while who whom why will with within without would
    you your yours yourself yourselves
    """.split()
)

#: Words that are never technologies on their own, even though they are
#: common in tech headlines.
TECH_STOPWORDS: frozenset[str] = frozenset(
    """
    ai api app apps build built building code coding compiler compute computer computers
    data database databases developer developers development dev docs documentation
    feature features file files framework free github google graph guide
    help issue issues job jobs key learn library linux list
    model models open page platform project python3 release repo repository research
    run running script server service services set setup show software solution source
    stack state story support system tech technology test testing tool tools tutorial
    update updates use user users version video web website windows work world
    year years
    best good great better next modern simple easy fast slow quick powerful
    ultimate perfect complete full comprehensive advanced efficient popular
    trending viral awesome amazing incredible thing things way ways really
    quite much lot lots
    local global remote native default custom standard official real time
    # Sentence-initial verbs. These are capitalised because they start a
    # headline, not because they name anything. "Working with Rust" is a
    # post about Rust, not a post about "Working".
    working trying building writing running talking creating making using
    getting seeing looking thinking knowing saying going doing coming taking
    learning teaching reading coding shipping launching starting stopping
    introducing announcing releasing building deploying scaling migrating
    managing leading driving powering securing testing monitoring profiling
    optimizing debugging refactoring documenting automating integrating
    # Post-type prefixes. "Ask HN:", "Show HN:" and "Tell HN:" name the
    # *kind* of post, not a technology. Without these, every "Ask HN:"
    # thread contributes a mention of a topic called "ask".
    ask show tell launch discuss
    # Generic nouns that tech headlines use constantly. They are not
    # technologies, but they are capitalised often enough in titles to
    # become recurring n-grams and reach the trend threshold — "The Ghost
    # in the Machine" is a film title, not a trend in ghost technology.
    ghost machine browser server cloud edge mobile desktop web
    engine core layer stack queue cache storage memory network system
    """.split()
)

#: The known technology vocabulary. Multi-word names come first so that
#: "machine learning" is matched before "machine" or "learning" separately.
KNOWN_TECHNOLOGIES: tuple[str, ...] = (
    # languages
    "python", "rust", "typescript", "javascript", "golang", "java", "kotlin", "swift",
    "ruby", "php", "scala", "haskell", "elixir", "erlang", "clojure", "zig", "c++",
    "ziglang",
    # runtimes and infra
    "kubernetes", "docker", "terraform", "ansible", "nginx", "aws", "azure", "gcp",
    "serverless", "linux", "postgres", "postgresql", "mysql", "sqlite", "redis",
    "kafka", "rabbitmq", "elasticsearch", "mongodb", "graphql", "grpc", "wasm",
    "webassembly", "microservices", "serverless", "cloudflare", "vercel", "netlify",
    # AI and ML
    "llm", "llms", "gpt", "openai", "anthropic", "claude", "gemini", "llama", "mistral",
    "huggingface", "pytorch", "tensorflow", "transformers", "transformer", "rag",
    "agentic", "agents", "mcp", "langchain", "llamacpp", "embedding", "embeddings",
    "finetuning", "inference", "multimodal", "diffusion", "artificial",
    "machine learning", "deep learning", "neural network", "neural networks",
    "copilot", "cursor", "ollama", "vllm", "chatgpt", "gemma", "qwen", "deepseek",
    "stable diffusion", "langgraph", "crewai", "agent framework",
    "retrieval augmented generation", "model context protocol",
    "large language model", "large language models",
    "prompt engineering", "prompt", "prompting", "token", "tokens", "context window",
    # frontend and web
    "react", "vue", "angular", "svelte", "nextjs", "remix", "astro", "vite",
    "webpack", "tailwind", "css", "html", "htmx", "electron", "tauri", "flutter",
    "reactnative",
    # mobile and desktop
    "ios", "android", "swiftui", "jetpack", "compose",
    # tooling
    "git", "github", "gitlab", "vim", "neovim", "emacs", "vscode", "jetbrains",
    "pytest", "jest", "pytest", "playwright", "cypress", "selenium", "poetry",
    "npm", "pnpm", "yarn", "pip", "cargo", "maven", "gradle",
    # protocols and formats
    "http", "https", "http2", "http3", "tcp", "udp", "dns", "tls", "ssl", "json",
    "yaml", "toml", "csv", "xml", "protobuf", "oauth", "jwt", "sso",
    # security
    "security", "encryption", "vulnerability", "cve", "malware", "phishing", "ransomware",
    # infra and data
    "kafka", "airflow", "dbt", "spark", "flink", "databricks", "snowflake", "bigquery",
    "clickhouse", "duckdb", "pandas", "numpy", "polars",
    # misc tech
    "chromium", "chrome", "firefox", "safari", "sqlite", "wasm",
    "obsidian", "notion", "figma", "discord", "slack", "matrix", "signal",
)

#: Normalised, deduplicated vocabulary — the multi-word names first.
_VOCABULARY: tuple[tuple[str, str], ...] = tuple(
    (tech, tech.lower())
    for tech in dict.fromkeys(KNOWN_TECHNOLOGIES)
)

#: A word is at least this long to be considered a candidate on its own.
MIN_WORD_LENGTH = 3

#: A capitalised phrase must reach this frequency to count as a topic.
MIN_NGRAM_FREQUENCY = 2

#: A capitalised phrase may be at most this many words long.
MAX_NGRAM_LENGTH = 4

#: Tags that identify the source or the *kind* of post rather than a
#: technology. `hackernews` says where a post came from; `discuss` says
#: what kind of dev.to post it is. Neither is a topic.
#:
#: This is the union of every adapter's `source_markers`, plus the platform
#: names. It is a module-level constant rather than something threaded
#: through the extractor because the answer does not depend on which
#: adapters ran — a tag that names a source names a source either way.
SOURCE_MARKERS: frozenset[str] = frozenset(
    {
        # platform names
        "hackernews",
        "github",
        "stackoverflow",
        "devto",
        "youtube",
        "rss",
        "reddit",
        # feed names
        "techcrunch",
        "theverge",
        "arxiv_ai",
        "arxiv_cs",
        # channel names
        "google_developers",
        # post-kind and community tags
        "discuss",
        "career",
        "beginners",
        "opensource",
        "productivity",
        "webdev",
        "devchallenge",
        "hacktoberfest",
        "community",
        "learning",
        "showdev",
        "help",
        "watercoower",
        "watercooler",
        "opportunities",
        "resources",
        "trusted",
        "software",
        "programming",
        "software engineering",
        "softwareengineering",
        "testing",
        "automation",
        "architecture",
        "best practices",
        "security",
        "cli",
        "api",
        "backend",
        "frontend",
        "fullstack",
        "database",
        "mobile",
        "cloud",
        "devtools",
        "tooling",
        "infrastructure",
        "observability",
        "performance",
        "scalability",
        "tutorial",
        "guide",
        "news",
        # repository-category labels that are not technologies
        "awesome",
        "awesome list",
        "awesome-list",
        "templates",
        "boilerplate",
        "starter",
        "example",
        "examples",
        "demo",
        "sample",
        "samples",
        "toolkit",
        "utilities",
        "utility",
        "tools",
        "hacking",
        "malware",
        "crack",
        "cracked",
        "activator",
        "license",
        "keygen",
        "nulled",
        "premium",
        "bundle",
        "collection",
        "pack",
        "repo",
        "mirror",
        "proxy",
        "config",
        "configs",
        "dotfiles",
        "notes",
        "cheatsheet",
        "roadmap",
        "interview",
        "interview-questions",
        "leetcode",
        "system-design",
        "cheatsheets",
        "projects",
        "project",
        "apps",
        "application",
        "applications",
        "stack",
        "awesome-ai",
        "ai-tools",
    }
)

_WORD_RE = re.compile(r"[a-z0-9+#.]+")

#: A capitalised phrase: a word that starts with a capital, optionally
#: followed by more capitalised or lowercase words.
#:
#: The first word must be capitalised, but the rest need not be — "ChatGPT
#: release" and "MCP server" are the shape of what people actually write.
#: Requiring every word to be capitalised misses both, because the phrase
#: that starts the match also swallows the capitalised word that follows.
#:
#: The run is matched generously and then trimmed at the word level, so the
#: decision about where a phrase ends is made in one place.
_NGRAM_RE = re.compile(
    r"\b[A-Z][A-Za-z0-9+#.]*"
    r"(?:\s+(?:[A-Z0-9][A-Za-z0-9+#.]*|[a-z][A-Za-z0-9+#.]*)){0,6}"
)

#: A capitalised word only starts a topic name if it begins the title or
#: follows a sentence boundary. "Working with Python" capitalises "Working"
#: because it starts the sentence, not because "Working" names anything.
#:
#: Without this, "Working with Python", "Working with Docker" and "Working
#: with Rust" all contribute a mention of the topic "Working", and a
#: generic verb ends up outranking every real technology.
_SENTENCE_START_RE = re.compile(r"(?:^|[.!?:]\s+)([A-Z])")

#: The matcher used when a caller does not pass one. It is None until
#: something sets it — the module does not build one on import, because
#: loading an embedding model is expensive and the radar must run without
#: it. `set_default_matcher` is called once by the pipeline, and the
#: pipeline calls it with whatever matcher it could actually build.
_DEFAULT_MATCHER: SemanticMatcher | None = None


def set_default_matcher(matcher: SemanticMatcher | None) -> None:
    """Set the matcher that `extract_topics` uses when given none.

    Passing None turns the semantic signal off. That is what the pipeline
    does when the embedding model is unavailable, and what the tests do
    when they want to check the lexical behaviour in isolation.
    """
    global _DEFAULT_MATCHER
    _DEFAULT_MATCHER = matcher


@dataclass(slots=True)
class TopicMatch:
    """One topic found in one post."""

    topic: str
    kind: str  # "known" | "ngram" | "tag" | "semantic"
    #: Where in the text it was found — the matched substring.
    surface: str = ""
    #: The similarity score, for a semantic match. Zero for the others.
    score: float = 0.0


@dataclass(slots=True)
class PostTopics:
    """The topics extracted from one post."""

    post_id: str
    platform: str
    title: str
    published: object
    weight: float
    topics: list[str] = field(default_factory=list)
    #: topic -> the text that matched it, for the evidence trail.
    evidence: dict[str, str] = field(default_factory=dict)
    #: topic -> which signal found it ("known" | "ngram" | "tag" | "semantic").
    kinds: dict[str, str] = field(default_factory=dict)
    url: str = ""
    raw_engagement: float = 0.0
    tags: tuple[str, ...] = ()


def _normalise_term(term: str) -> str:
    return term.strip().lower().strip(".,:;!?()[]{}\"'`")


def _is_meaningful(word: str) -> bool:
    if len(word) < MIN_WORD_LENGTH:
        return False
    if word in STOPWORDS or word in TECH_STOPWORDS:
        return False
    return not word.isdigit()


def _matches_known(text: str) -> dict[str, str]:
    """Find known technologies in a text. Multi-word names win."""
    lowered = text.lower()
    found: dict[str, str] = {}

    for tech, canonical in _VOCABULARY:
        if canonical in SOURCE_MARKERS:
            continue
        if " " in tech:
            pattern = r"(?<![a-z0-9])" + re.escape(tech) + r"(?![a-z0-9])"
        else:
            pattern = r"(?<![a-z0-9+#])" + re.escape(tech) + r"(?![a-z0-9+#])"
        match = re.search(pattern, lowered)
        if match:
            found[canonical_topic(canonical)] = match.group(0)
    return found


def _is_known_term(word: str) -> bool:
    """Whether a single word names a technology we already recognise."""
    canonical = canonical_topic(_normalise_term(word))
    return bool(canonical) and canonical not in SOURCE_MARKERS


def _ngrams(text: str) -> list[str]:
    """Capitalised phrases in the text.

    Only the first word of a phrase needs to be capitalised for the phrase to
    count — "MCP server" has a lowercase second word, and so does most of
    what people actually write.

    The phrase is the run of meaningful words that *starts* at a
    capitalised word. A phrase stops at the first word that is not
    meaningful, rather than being rejected because a later word was not.

    Every prefix of that run is emitted, not just the whole thing.
    "Widgetron benchmarks" produces both "Widgetron benchmarks" and
    "Widgetron". The shorter one is the technology name and the longer
    one is the name plus a word describing the post; which one is the
    topic depends on what recurs across the corpus, which is decided
    later. Emitting only the full run would split "Widgetron" and
    "Widgetron benchmarks" into two topics that each have half the
    evidence.

    Leading stopwords are trimmed for the same reason — without the trim,
    the same technology written three different ways would look like
    three different topics.
    """
    results: list[str] = []
    # Where does a capitalised word start a sentence? Only there can a
    # capitalised word be naming something.
    sentence_starts = {m.start(1) for m in _SENTENCE_START_RE.finditer(text)}

    for match in _NGRAM_RE.finditer(text):
        # The match must begin at a sentence boundary. `match.start()` is
        # the position of the capitalised word itself, because the regex
        # starts with `\b[A-Z]`.
        if match.start() not in sentence_starts:
            continue

        words = match.group(0).strip().split()
        if not words:
            continue

        # Skip a leading stopword: "The Widgetron" starts with "The".
        # The word that heads the phrase must still be capitalised —
        # skipping past "Working with" and landing on a lowercase "docker"
        # would turn a sentence into a topic name.
        start = 0
        while start < len(words) and not _is_meaningful(_normalise_term(words[start])):
            start += 1
        if start >= len(words):
            continue
        if not words[start][:1].isupper():
            continue

        # Take the run of meaningful words from there, up to the limit.
        #
        # The run stops at a word that is itself a known technology.
        # "LLM works best locally" would otherwise yield "LLM works best"
        # alongside "LLM" — and the longer phrase is not a topic, it is the
        # topic plus a sentence. Stopping at the technology keeps the
        # name clean and lets the known-vocabulary path own it.
        end = start
        while (
            end < len(words)
            and end - start < MAX_NGRAM_LENGTH
            and _is_meaningful(_normalise_term(words[end]))
        ):
            end += 1
            if end - start >= 1 and _is_known_term(words[end - 1]):
                break

        # Every prefix of the run is a candidate.
        for length in range(1, end - start + 1):
            results.append(" ".join(words[start : start + length]))
    return results


def extract_topics(
    title: str,
    description: str = "",
    tags: tuple[str, ...] = (),
    semantic: SemanticMatcher | None = None,
) -> list[TopicMatch]:
    """Extract the topics from one post.

    Returns the matches found, in the order they were discovered. The same
    topic is never returned twice.

    `semantic` is an optional `SemanticMatcher`. When it is given — or when
    the module-level default has been set — a post that names a technology
    the vocabulary does not know still contributes a mention to the nearest
    topic the vocabulary does know. When the matcher is unavailable, the
    lexical signals are used alone and nothing else changes.
    """
    matches: list[TopicMatch] = []
    seen: set[str] = set()

    def add(topic: str, kind: str, surface: str = "", score: float = 0.0) -> None:
        canonical = canonical_topic(_normalise_term(topic))
        if not canonical or canonical in seen:
            return
        if is_person_name(canonical):
            return
        seen.add(canonical)
        matches.append(
            TopicMatch(topic=canonical, kind=kind, surface=surface or topic, score=score)
        )

    # 1. Known technologies. Search the title first — a headline names the
    #    technology, a description mentions it in passing.
    for text in (title, description):
        if not text:
            continue
        for canonical, surface in _matches_known(text).items():
            add(canonical, "known", surface)

    # 2. Platform tags. A tag is already a normalised topic label — unless
    #    it names the source or the kind of post, in which case it is not a
    #    topic at all.
    for tag in tags:
        canonical = _normalise_term(tag.replace("-", " "))
        if canonical in SOURCE_MARKERS:
            continue
        if canonical and _is_meaningful(canonical):
            add(canonical, "tag", tag)

    # 3. Capitalised phrases. These are kept only if they recur across the
    #    corpus, so the caller filters on frequency — `extract_topics` marks
    #    them but does not decide.
    for phrase in _ngrams(title):
        add(_normalise_term(phrase), "ngram", phrase)

    # 4. Semantic match. Last, so that a topic the lexical signals already
    #    found is owned by them — the evidence trail should show the actual
    #    word that appeared, not a similarity score.
    matcher = semantic if semantic is not None else _DEFAULT_MATCHER
    if matcher is not None and matcher.available:
        result = matcher.match(title, description)
        for match in result.matches:
            add(match.topic, "semantic", title, match.score)

    return matches


#: Technologies that are the same thing under different names. When two
#: topics in a pair are both found, they are merged into the canonical one
#: rather than counted separately — otherwise `copilot`, `github copilot`
#: and `microsoft copilot` each get a third of the mentions and none of
#: them reaches the threshold that tells you it is a real trend.
TOPIC_ALIASES: dict[str, str] = {
    "github copilot": "copilot",
    "microsoft copilot": "copilot",
    "copilot chat": "copilot",
    "vs code": "vscode",
    "visual studio code": "vscode",
    "gpt 4": "gpt",
    "gpt 4o": "gpt",
    "chat gpt": "chatgpt",
    "post gres": "postgres",
    "postgre sql": "postgres",
    "golang": "go",
    "google cloud platform": "gcp",
    "amazon web services": "aws",
    "node js": "nodejs",
    "next js": "nextjs",
    "next.js": "nextjs",
    "node.js": "nodejs",
    "vue.js": "vue",
    "react.js": "react",
    "react js": "react",
    "type script": "typescript",
    "java script": "javascript",
    "kuber netes": "kubernetes",
    "machine learning": "machine learning",
    "large language model": "llm",
    "large language models": "llm",
    "llm s": "llm",
    "llms": "llm",
    "llm agents": "llm",
    "agentic ai": "agentic",
    "tokens": "token",
    "embeddings": "embedding",
    "agents": "agent",
    "systems": "system",
    "apis": "api",
    "databases": "database",
    "frameworks": "framework",
    "repositories": "repository",
    "releases": "release",
    "versions": "version",
    "tools": "tool",
    "models": "model",
    "services": "service",
    "platforms": "platform",
    "languages": "language",
    "compilers": "compiler",
    "containers": "container",
    "clusters": "cluster",
    "pipelines": "pipeline",
    "retrieval augmented generation": "rag",
    "model context protocol": "mcp",
    "web assembly": "webassembly",
    "pytorch": "pytorch",
    "tensor flow": "tensorflow",
    "artificial intelligence": "artificial intelligence",
    "ip tv": "iptv",
}


#: Names of people who appear in tech headlines. A person's name is news,
#: not a technology — "Jensen Huang" is not a trend in the same sense that
#: "Nvidia" is. Companies are separate: a company *is* a technology topic,
#: because "Nvidia shipping X" is a genuine trend.
PERSON_NAMES: frozenset[str] = frozenset(
    {
        "jensen huang",
        "elon musk",
        "sam altman",
        "sundar pichai",
        "satya nadella",
        "tim cook",
        "mark zuckerberg",
        "jeff bezos",
        "demis hassabis",
        "dario amodei",
        "mira murati",
        "greg brockman",
        "andrej karpathy",
        "ilya sutskever",
        "yann lecun",
        "geoffrey hinton",
        "guido van rossum",
        "linus torvalds",
        "james gosling",
        "bjarne stroustrup",
        "richard henderson",
        "gordon moore",
        "alan turing",
    }
)


def is_person_name(topic: str) -> bool:
    """Whether a topic is a person's name rather than a technology.

    A prefix of a person's name counts too. "Jensen Huang" is a person, and
    so is "Jensen" once it has been split off by the phrase extractor — both
    are news about a person, not a technology.
    """
    normalised = topic.strip().lower()
    if normalised in PERSON_NAMES:
        return True
    return any(name.startswith(normalised + " ") for name in PERSON_NAMES)


def canonical_topic(topic: str) -> str:
    """The canonical name for a topic, following the alias table."""
    return TOPIC_ALIASES.get(topic.strip().lower(), topic.strip().lower())


def ngram_candidates(posts: list[PostTopics]) -> dict[str, int]:
    """How often each capitalised phrase appears across the corpus.

    A phrase that appears in only one post is that post's title, not a
    technology. Requiring recurrence is what separates the two.

    Where one phrase is a prefix of another — "widgetron" and "widgetron
    benchmarks" — the shorter one wins. The short form is the name and the
    long form adds a word that describes the post; splitting the evidence
    between them would leave neither with enough to clear the bar.
    """
    counts: Counter[str] = Counter()
    for post in posts:
        for match in extract_topics(post.title):
            if match.kind == "ngram":
                counts[canonical_topic(match.topic)] += 1

    recurring = {k: v for k, v in counts.items() if v >= MIN_NGRAM_FREQUENCY}

    # Drop a phrase when a shorter recurring phrase is a prefix of it.
    prefixes = list(recurring)
    return {
        phrase: count
        for phrase, count in recurring.items()
        if not any(
            shorter != phrase and phrase.startswith(shorter + " ")
            for shorter in prefixes
        )
    }


def topics_for_post(
    post,
    ngram_whitelist: set[str] | None = None,
    semantic: SemanticMatcher | None = None,
) -> list[str]:
    """The topics for one post, after applying the corpus-wide n-gram filter.

    `ngram_whitelist` holds the phrases that recurred often enough to count.
    Phrases outside it are dropped — unless they are also known technologies
    or platform tags, which are already trusted.
    """
    matches = extract_topics(post.title, post.description, post.tags, semantic=semantic)
    topics: list[str] = []
    for match in matches:
        if match.kind == "ngram":
            if ngram_whitelist is not None and match.topic not in ngram_whitelist:
                continue
        topics.append(match.topic)
    return topics
