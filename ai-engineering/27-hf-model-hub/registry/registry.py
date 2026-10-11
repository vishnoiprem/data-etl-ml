"""Hugging Face-style model registry: versioning + license gate + tags + lineage.

The shape behind HF Hub: a registry of models, each with a version
line, a license, an eval table, download stats, tags, and lineage
(parent / children). The license gate is the part that matters in
production — a non-commercial-licensed model cannot be served
commercially.
"""
from __future__ import annotations
import time
from dataclasses import dataclass, field


COMMERCIAL_LICENSES = {"apache-2.0", "mit", "bsd-3-clause", "llama3-community"}
NON_COMMERCIAL_LICENSES = {"cc-by-nc-4.0", "research-only", "cc-by-nc-sa-4.0"}


@dataclass
class ModelVersion:
    sha: str
    eval_table: dict = field(default_factory=dict)  # {"mmlu": 0.62, "gsm8k": 0.41}
    downloads: int = 0
    artifact_uri: str = ""


@dataclass
class Model:
    name: str                     # "my-org/llama-3-8b-finetune"
    license: str
    versions: list[ModelVersion] = field(default_factory=list)
    gated: bool = False
    tags: set[str] = field(default_factory=set)
    likes: int = 0
    parent: str | None = None    # name of the base model this was fine-tuned from

    def latest(self) -> "ModelVersion | None":
        return self.versions[-1] if self.versions else None

    def can_serve_commercially(self) -> bool:
        return self.license.lower() in COMMERCIAL_LICENSES

    def total_downloads(self) -> int:
        return sum(v.downloads for v in self.versions)


@dataclass
class Hub:
    models: dict[str, Model] = field(default_factory=dict)
    blocked_licenses: set[str] = field(default_factory=lambda: NON_COMMERCIAL_LICENSES.copy())

    def publish(self, model: "Model", version: "ModelVersion") -> None:
        if model.name not in self.models:
            self.models[model.name] = model
        self.models[model.name].versions.append(version)

    def serve_url(self, name: str, commercial: bool) -> "str | None":
        m = self.models.get(name)
        if m is None:
            return None
        if commercial and not m.can_serve_commercially():
            return None
        v = m.latest()
        if v is None:
            return None
        return f"hub://{name}@{v.sha}"

    def list_licenses(self) -> dict:
        out: dict[str, int] = {}
        for m in self.models.values():
            out[m.license] = out.get(m.license, 0) + 1
        return out

    def search_by_tag(self, tag: str) -> list["Model"]:
        """Return all models that have `tag` in their tag set."""
        return [m for m in self.models.values() if tag in m.tags]

    def parent_of(self, name: str) -> "Model | None":
        m = self.models.get(name)
        if m is None or m.parent is None:
            return None
        return self.models.get(m.parent)

    def children_of(self, name: str) -> list["Model"]:
        return [m for m in self.models.values() if m.parent == name]

    def ranking_by_downloads(self) -> list["Model"]:
        """Most-downloaded first. Stable: ties broken by name for determinism."""
        return sorted(
            self.models.values(),
            key=lambda m: (-m.total_downloads(), m.name),
        )


# === meaningful workload ===
CATALOG: list[dict] = [
    # name, license, tags, parent, likes, n_versions
    {"name": "acme/llama-3-8b-base",            "license": "llama3-community", "tags": {"text-generation", "llama", "base", "english", "8b"},
     "parent": None,                              "likes": 4_200, "n_versions": 3},
    {"name": "acme/llama-3-8b-instruct",        "license": "llama3-community", "tags": {"text-generation", "instruct", "chat", "english", "8b"},
     "parent": "acme/llama-3-8b-base",            "likes": 6_100, "n_versions": 4},
    {"name": "acme/llama-3-8b-code",            "license": "apache-2.0",       "tags": {"text-generation", "code", "python", "english", "8b"},
     "parent": "acme/llama-3-8b-base",            "likes": 3_400, "n_versions": 3},
    {"name": "acme/llama-3-8b-medical",         "license": "research-only",    "tags": {"text-generation", "medical", "english", "8b", "domain-specific"},
     "parent": "acme/llama-3-8b-instruct",        "likes": 1_900, "n_versions": 3},
    {"name": "acme/llama-3-8b-ko",              "license": "apache-2.0",       "tags": {"text-generation", "korean", "multilingual", "8b", "translation"},
     "parent": "acme/llama-3-8b-base",            "likes": 1_200, "n_versions": 3},
    {"name": "acme/mistral-7b-base",            "license": "apache-2.0",       "tags": {"text-generation", "mistral", "base", "english", "7b"},
     "parent": None,                              "likes": 5_500, "n_versions": 4},
    {"name": "acme/mistral-7b-instruct",        "license": "apache-2.0",       "tags": {"text-generation", "instruct", "chat", "english", "7b"},
     "parent": "acme/mistral-7b-base",            "likes": 7_800, "n_versions": 4},
    {"name": "acme/mistral-7b-fr",              "license": "apache-2.0",       "tags": {"text-generation", "french", "multilingual", "7b", "translation"},
     "parent": "acme/mistral-7b-base",            "likes": 980,   "n_versions": 3},
    {"name": "acme/bert-base-uncased",          "license": "apache-2.0",       "tags": {"fill-mask", "bert", "english", "base", "encoder"},
     "parent": None,                              "likes": 9_200, "n_versions": 5},
    {"name": "acme/bert-sentiment-finetuned",   "license": "apache-2.0",       "tags": {"text-classification", "sentiment", "english", "bert"},
     "parent": "acme/bert-base-uncased",          "likes": 2_700, "n_versions": 3},
    {"name": "acme/bert-ner-finetuned",         "license": "apache-2.0",       "tags": {"token-classification", "ner", "english", "bert"},
     "parent": "acme/bert-base-uncased",          "likes": 1_600, "n_versions": 3},
    {"name": "acme/distilbert-6-base",          "license": "apache-2.0",       "tags": {"fill-mask", "distilbert", "english", "base", "encoder"},
     "parent": "acme/bert-base-uncased",          "likes": 3_300, "n_versions": 3},
    {"name": "acme/vit-base-patch16",           "license": "apache-2.0",       "tags": {"image-classification", "vision", "vit", "base", "encoder"},
     "parent": None,                              "likes": 4_400, "n_versions": 4},
    {"name": "acme/vit-finetuned-cifar10",      "license": "mit",              "tags": {"image-classification", "vision", "vit", "cifar10"},
     "parent": "acme/vit-base-patch16",           "likes": 1_100, "n_versions": 3},
    {"name": "acme/clip-vit-base",              "license": "mit",              "tags": {"zero-shot-classification", "multimodal", "clip", "vision", "english"},
     "parent": None,                              "likes": 6_700, "n_versions": 3},
    {"name": "acme/whisper-small",              "license": "apache-2.0",       "tags": {"automatic-speech-recognition", "whisper", "multilingual", "audio", "encoder-decoder"},
     "parent": None,                              "likes": 5_900, "n_versions": 4},
    {"name": "acme/whisper-small-en",           "license": "apache-2.0",       "tags": {"automatic-speech-recognition", "whisper", "english", "audio"},
     "parent": "acme/whisper-small",              "likes": 1_400, "n_versions": 3},
    {"name": "acme/t5-small-base",              "license": "apache-2.0",       "tags": {"text2text-generation", "t5", "base", "english", "encoder-decoder"},
     "parent": None,                              "likes": 3_800, "n_versions": 3},
    {"name": "acme/t5-small-summarizer",        "license": "apache-2.0",       "tags": {"text2text-generation", "summarization", "t5", "english"},
     "parent": "acme/t5-small-base",              "likes": 1_300, "n_versions": 3},
    {"name": "acme/stable-diffusion-1.5",       "license": "creeml-open-rail-m", "tags": {"text-to-image", "diffusion", "multimodal", "english", "vision"},
     "parent": None,                              "likes": 8_400, "n_versions": 3},
    {"name": "acme/sd-1.5-anime",               "license": "creeml-open-rail-m", "tags": {"text-to-image", "diffusion", "anime", "vision"},
     "parent": "acme/stable-diffusion-1.5",       "likes": 2_200, "n_versions": 3},
    {"name": "acme/research-only-rlhf-7b",      "license": "cc-by-nc-4.0",     "tags": {"text-generation", "rlhf", "research", "english", "7b"},
     "parent": "acme/llama-3-8b-base",            "likes": 600,   "n_versions": 3},
]


# Pseudo-realistic download curves: power law, with the more popular / instruct
# / base models pulling a long tail.
def _downloads_for(model_name: str, version_idx: int, n_versions: int) -> int:
    # Base: how popular the model is (very rough; tuned for ranking variation)
    base = {
        "acme/llama-3-8b-base":            180_000,
        "acme/llama-3-8b-instruct":        420_000,
        "acme/llama-3-8b-code":            230_000,
        "acme/llama-3-8b-medical":          45_000,
        "acme/llama-3-8b-ko":               38_000,
        "acme/mistral-7b-base":            210_000,
        "acme/mistral-7b-instruct":        510_000,
        "acme/mistral-7b-fr":               29_000,
        "acme/bert-base-uncased":          780_000,
        "acme/bert-sentiment-finetuned":   145_000,
        "acme/bert-ner-finetuned":          88_000,
        "acme/distilbert-6-base":          195_000,
        "acme/vit-base-patch16":           320_000,
        "acme/vit-finetuned-cifar10":       72_000,
        "acme/clip-vit-base":              410_000,
        "acme/whisper-small":              265_000,
        "acme/whisper-small-en":            92_000,
        "acme/t5-small-base":              175_000,
        "acme/t5-small-summarizer":         81_000,
        "acme/stable-diffusion-1.5":       620_000,
        "acme/sd-1.5-anime":               155_000,
        "acme/research-only-rlhf-7b":       18_000,
    }.get(model_name, 50_000)
    # Distribute across versions: newest versions get more downloads, oldest
    # got the long tail. Weights: [1, 1.5, 2.2, 3.0, 4.0] but bounded by n_versions.
    weights = [1.0, 1.5, 2.2, 3.0, 4.0]
    w = weights[min(version_idx, len(weights) - 1)]
    return int(base * w / sum(weights[:n_versions]))


def _eval_table_for(name: str) -> dict:
    # Plausible benchmark scores; not real numbers, but stable per model
    seed = abs(hash(name)) % 1000
    return {
        "mmlu":    round(0.45 + (seed % 40) / 100.0, 3),
        "gsm8k":   round(0.20 + ((seed * 3) % 50) / 100.0, 3),
        "hellaswag": round(0.50 + ((seed * 5) % 35) / 100.0, 3),
    }


def build_catalog() -> Hub:
    """Construct a Hub with a realistic 22-model / multi-version catalog."""
    hub = Hub()
    for spec in CATALOG:
        m = Model(
            name=spec["name"],
            license=spec["license"],
            tags=set(spec["tags"]),
            likes=spec["likes"],
            parent=spec["parent"],
        )
        for v in range(spec["n_versions"]):
            sha = f"sha-{spec['name'].split('/')[-1]}-v{v}"
            dl = _downloads_for(spec["name"], v, spec["n_versions"])
            hub.publish(m, ModelVersion(
                sha=sha,
                eval_table=_eval_table_for(spec["name"]),
                downloads=dl,
                artifact_uri=f"s3://artifacts/{spec['name']}@{sha}",
            ))
    return hub


def assert_unique_ids(hub: Hub) -> None:
    names = list(hub.models.keys())
    assert len(names) == len(set(names)), f"duplicate model IDs: {names}"
    assert len(names) == 0 or all("" != n for n in names), "empty model name"


def assert_version_counts(hub: Hub, expected: dict[str, int]) -> None:
    for name, n in expected.items():
        assert hub.models[name].versions.__len__() == n, (
            f"{name}: expected {n} versions, got {len(hub.models[name].versions)}"
        )


def assert_search_by_tag(hub: Hub, tag: str) -> list[Model]:
    results = hub.search_by_tag(tag)
    assert results, f"no models found for tag {tag!r}"
    for m in results:
        assert tag in m.tags, f"search returned {m.name!r} which lacks tag {tag!r}"
    return results


def assert_lineage(hub: Hub, child_name: str, expected_parent: str) -> None:
    p = hub.parent_of(child_name)
    assert p is not None, f"{child_name} has no parent recorded"
    assert p.name == expected_parent, f"{child_name}: parent {p.name} != {expected_parent}"


def assert_children(hub: Hub, parent_name: str, expected_min: int) -> list[Model]:
    kids = hub.children_of(parent_name)
    assert len(kids) >= expected_min, (
        f"{parent_name}: expected >= {expected_min} children, got {len(kids)}"
    )
    for k in kids:
        assert k.parent == parent_name, f"{k.name}.parent != {parent_name}"
    return kids


def assert_ranking_consistent(hub: Hub) -> Model:
    ranked = hub.ranking_by_downloads()
    assert ranked, "ranking is empty"
    top = ranked[0]
    top_dl = top.total_downloads()
    for m in ranked[1:]:
        assert top_dl >= m.total_downloads(), (
            f"ranking broken: top {top.name} ({top_dl}) < {m.name} ({m.total_downloads()})"
        )
    return top


if __name__ == "__main__":
    print("═══ hf-model-hub: meaningful workload ═══")

    # ---------- Scenario A: register, add versions, verify registry ----------
    print("\n[A] register catalog (22 models, multi-version) and verify")
    t0 = time.time()
    hub = build_catalog()
    build_s = time.time() - t0
    expected_versions = {spec["name"]: spec["n_versions"] for spec in CATALOG}
    expected_n_models = len(CATALOG)
    expected_total_downloads = sum(
        _downloads_for(spec["name"], v, spec["n_versions"])
        for spec in CATALOG
        for v in range(spec["n_versions"])
    )
    assert_unique_ids(hub)
    assert len(hub.models) == expected_n_models
    assert_version_counts(hub, expected_versions)
    print(f"  models registered:   {len(hub.models)}")
    print(f"  total versions:      {sum(len(m.versions) for m in hub.models.values())}")
    print(f"  total downloads:     {expected_total_downloads:,}")
    print(f"  build time:          {build_s * 1000:.2f} ms")
    print(f"  license distribution:{hub.list_licenses()}")
    print("  ✓ every model has a unique ID and the expected version count")

    # ---------- Scenario B: search by tag, verify no false positives ----------
    print("\n[B] search by tag — no false positives allowed")
    for tag in ("text-generation", "image-classification", "text-to-image", "fill-mask",
                "automatic-speech-recognition", "text2text-generation"):
        t0 = time.time()
        results = assert_search_by_tag(hub, tag)
        dt_ms = (time.time() - t0) * 1000
        names = ", ".join(m.name for m in results[:3])
        more = f" (+{len(results) - 3} more)" if len(results) > 3 else ""
        print(f"  tag={tag:<32} hits={len(results):>3}  search={dt_ms:6.2f} ms  e.g. {names}{more}")
    print("  ✓ all returned models actually carry the searched tag")

    # ---------- Scenario C: lineage — parent + children ----------
    print("\n[C] lineage — parent of a fine-tune, children of a base")
    assert_lineage(hub, "acme/llama-3-8b-instruct",     "acme/llama-3-8b-base")
    assert_lineage(hub, "acme/llama-3-8b-medical",      "acme/llama-3-8b-instruct")
    assert_lineage(hub, "acme/bert-sentiment-finetuned","acme/bert-base-uncased")
    assert_lineage(hub, "acme/sd-1.5-anime",            "acme/stable-diffusion-1.5")
    print("  ✓ parent pointers resolve: instruct→base, medical→instruct, "
          "bert-sentiment→bert, sd-anime→sd-1.5")

    children = assert_children(hub, "acme/llama-3-8b-base", expected_min=4)
    print(f"  base 'acme/llama-3-8b-base' has {len(children)} descendants: "
          f"{[c.name for c in children]}")
    children_bert = assert_children(hub, "acme/bert-base-uncased", expected_min=3)
    print(f"  base 'acme/bert-base-uncased' has {len(children_bert)} descendants: "
          f"{[c.name for c in children_bert]}")
    print("  ✓ every base model has its children; every child records its parent")

    # ---------- Scenario D: popularity ranking by downloads ----------
    print("\n[D] popularity ranking by downloads")
    t0 = time.time()
    top = assert_ranking_consistent(hub)
    rank_ms = (time.time() - t0) * 1000
    print(f"  top model:        {top.name}  ({top.total_downloads():,} downloads, "
          f"{top.likes:,} likes)")
    ranked = hub.ranking_by_downloads()
    print(f"  ranking computed in {rank_ms:.2f} ms")
    print(f"  top 5 by downloads:")
    for i, m in enumerate(ranked[:5], 1):
        print(f"    {i}. {m.name:<40} {m.total_downloads():>10,} dl  "
              f"({len(m.versions)} versions, {m.likes:,} likes)")

    # Bonus: license gate still works on the populated hub
    print("\n[gate] commercial serve URL spot-checks on the populated hub")
    commercial_ok = hub.serve_url("acme/llama-3-8b-instruct", commercial=True)
    blocked = hub.serve_url("acme/research-only-rlhf-7b", commercial=True)
    research_ok = hub.serve_url("acme/research-only-rlhf-7b", commercial=False)
    assert commercial_ok is not None and commercial_ok.startswith("hub://")
    assert blocked is None, "non-commercial model was served commercially"
    assert research_ok is not None
    print(f"  commercial  llama-instruct      -> {commercial_ok}")
    print(f"  commercial  research-only-rlhf  -> {blocked}   (must be None)")
    print(f"  research    research-only-rlhf  -> {research_ok}")

    # ---------- final invariants ----------
    print("\n[invariants]")
    assert_unique_ids(hub)
    assert len(hub.models) == expected_n_models
    assert_version_counts(hub, expected_versions)
    assert_search_by_tag(hub, "text-generation")
    assert_lineage(hub, "acme/llama-3-8b-medical", "acme/llama-3-8b-instruct")
    assert_children(hub, "acme/llama-3-8b-base", 4)
    assert_ranking_consistent(hub)
    print("  ✓ all invariants pass")
