import re

class QueryPlanner:
    EXACT = [r"\b(?:ORD|ORDER)[-_]?\d{4,}\b", r"\bSKU[-_]?\d{4,}\b", r"\bINV[-_]?\d{4,}\b"]
    SYNONYMS = {"mcp": "model context protocol tool contract", "rag": "retrieval augmented generation", "bloat": "excess irrelevant context", "retry": "transient failure repeat", "resume": "checkpoint continue"}

    def exact_id(self, query: str):
        for pattern in self.EXACT:
            match = re.search(pattern, query, re.I)
            if match:
                return match.group(0).upper()
        return None

    def classify(self, query: str) -> str:
        if self.exact_id(query):
            return "exact_lookup"
        if any(x in query.lower() for x in ["why", "compare", "evaluate", "analyze"]):
            return "analytical"
        return "search"

    def rewrite(self, query: str) -> str:
        words = re.sub(r"\s+", " ", query.lower().strip()).split()
        out = []
        for word in words:
            out.append(word)
            clean = re.sub(r"[^a-z0-9]", "", word)
            if clean in self.SYNONYMS:
                out.extend(self.SYNONYMS[clean].split())
        return " ".join(out)

    def fan_out(self, query: str, limit: int = 4) -> list[str]:
        base = self.rewrite(query)
        variants = [base, f"{base} policy standard", f"{base} architecture implementation", f"{base} evaluation metrics"]
        return list(dict.fromkeys(variants))[:limit]
