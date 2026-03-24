"""
Prompt Engineering Module — 15 prompt strategies with template versioning.

Strategies: zero_shot, few_shot, chain_of_thought, react, tree_of_thought,
            reflexion, program_of_thought, role, meta, skeleton_of_thought,
            rag, directional, self_consistency, zero_shot_cot, step_back
"""

from __future__ import annotations

from typing import Any

from ai_core.schemas import PromptStrategy, PromptTemplate


# ── Strategy Renderers ───────────────────────────────────────────────────────

_STRATEGY_TEMPLATES: dict[PromptStrategy, str] = {
    PromptStrategy.ZERO_SHOT: "{system}\n\n{query}",
    PromptStrategy.FEW_SHOT: (
        "{system}\n\nExamples:\n{examples}\n\nNow answer:\n{query}"
    ),
    PromptStrategy.CHAIN_OF_THOUGHT: (
        "{system}\n\nThink step by step.\n\n{query}\n\nLet's work through this step by step:"
    ),
    PromptStrategy.ZERO_SHOT_COT: (
        "{system}\n\n{query}\n\nLet's think step by step."
    ),
    PromptStrategy.REACT: (
        "{system}\n\nUse the following format:\n"
        "Thought: think about what to do\n"
        "Action: the action to take\n"
        "Action Input: the input to the action\n"
        "Observation: the result of the action\n"
        "... (repeat as needed)\n"
        "Final Answer: the final answer\n\n"
        "Question: {query}"
    ),
    PromptStrategy.TREE_OF_THOUGHT: (
        "{system}\n\nExplore multiple reasoning paths for the following problem. "
        "For each path, evaluate its promise before continuing.\n\n{query}"
    ),
    PromptStrategy.REFLEXION: (
        "{system}\n\nAnswer the question. Then reflect on your answer and correct any mistakes.\n\n"
        "{query}\n\nInitial Answer:\n\nReflection:\n\nFinal Answer:"
    ),
    PromptStrategy.PROGRAM_OF_THOUGHT: (
        "{system}\n\nSolve this by writing Python code to compute the answer.\n\n"
        "{query}\n\n```python\n# Solution\n```"
    ),
    PromptStrategy.ROLE: (
        "You are {role}.\n\n{system}\n\n{query}"
    ),
    PromptStrategy.META: (
        "{system}\n\nGenerate an optimized prompt for the following task:\n\n{query}"
    ),
    PromptStrategy.SKELETON_OF_THOUGHT: (
        "{system}\n\nFirst, provide a skeleton outline of the answer. "
        "Then fill in each point with details.\n\n{query}"
    ),
    PromptStrategy.RAG: (
        "{system}\n\nContext:\n{context}\n\nBased on the context above, answer the following:\n{query}"
    ),
    PromptStrategy.DIRECTIONAL: (
        "{system}\n\nHint: {hint}\n\n{query}"
    ),
    PromptStrategy.SELF_CONSISTENCY: (
        "{system}\n\nAnswer the following question {n} times independently, "
        "then select the most consistent answer.\n\n{query}"
    ),
    PromptStrategy.STEP_BACK: (
        "{system}\n\nBefore answering, first consider the broader principle or concept behind this question.\n\n"
        "Step-back question: {step_back}\n\nOriginal question: {query}"
    ),
}


class PromptEngine:
    """Build and render prompts with configurable strategies."""

    def __init__(self) -> None:
        self._templates: dict[str, str] = {}

    def build(
        self,
        *,
        technique: str | PromptStrategy = PromptStrategy.ZERO_SHOT,
        system: str = "",
        query: str = "",
        context: str | list[str] = "",
        examples: list[dict[str, str]] | None = None,
        role: str = "a helpful assistant",
        hint: str = "",
        n: int = 3,
        step_back: str = "",
        **kwargs: Any,
    ) -> str:
        """Render a prompt using the given strategy."""
        strategy = PromptStrategy(technique) if isinstance(technique, str) else technique
        template = _STRATEGY_TEMPLATES.get(strategy, "{system}\n\n{query}")

        # Format examples
        examples_str = ""
        if examples:
            examples_str = "\n".join(
                f"Q: {ex.get('question', ex.get('input', ''))}\n"
                f"A: {ex.get('answer', ex.get('output', ''))}"
                for ex in examples
            )

        # Format context
        if isinstance(context, list):
            context = "\n\n".join(context)

        return template.format(
            system=system,
            query=query,
            context=context,
            examples=examples_str,
            role=role,
            hint=hint,
            n=n,
            step_back=step_back or f"What is the underlying principle for: {query}",
            **kwargs,
        )

    async def execute(
        self,
        prompt: str,
        llm: Any,
        *,
        model: str | None = None,
        **kwargs: Any,
    ) -> Any:
        """Execute an already-rendered prompt against an LLM."""
        return await llm.generate(prompt, **kwargs)


# ── Prompt Registry ──────────────────────────────────────────────────────────


class PromptRegistry:
    """Versioned prompt template registry."""

    _templates: dict[str, list[PromptTemplate]] = {}

    @classmethod
    def register(cls, template: PromptTemplate) -> PromptTemplate:
        """Register a new prompt template version."""
        key = template.name
        if key not in cls._templates:
            cls._templates[key] = []
        # Auto-increment version
        existing = cls._templates[key]
        template.version = len(existing) + 1
        cls._templates[key].append(template)
        return template

    @classmethod
    def render(cls, name: str, **kwargs: Any) -> str:
        """Render the latest version of a named template."""
        versions = cls._templates.get(name)
        if not versions:
            raise KeyError(f"Template not found: {name}")
        template = versions[-1]
        engine = PromptEngine()
        return engine.build(
            technique=template.strategy,
            system=template.system,
            query=template.user_template.format(**kwargs) if kwargs else template.user_template,
            examples=template.examples,
        )

    @classmethod
    def list(cls, domain: str | None = None) -> list[str]:
        """List all registered template names, optionally filtered by domain."""
        if domain:
            return [
                name
                for name, versions in cls._templates.items()
                if versions[-1].metadata.get("domain") == domain
            ]
        return list(cls._templates.keys())

    @classmethod
    def get_versions(cls, name: str) -> list[PromptTemplate]:
        """Get all versions of a template."""
        return list(cls._templates.get(name, []))

    @classmethod
    def rollback(cls, name: str, version: int) -> PromptTemplate:
        """Set a specific version as the active (latest) version."""
        versions = cls._templates.get(name)
        if not versions:
            raise KeyError(f"Template not found: {name}")
        target = next((v for v in versions if v.version == version), None)
        if target is None:
            raise ValueError(f"Version {version} not found for template: {name}")
        # Move to end (latest)
        versions.remove(target)
        versions.append(target)
        return target

    @classmethod
    def clear(cls) -> None:
        """Clear all registered templates."""
        cls._templates.clear()


# ── Dynamic Example Selector ────────────────────────────────────────────────


class DynamicExampleSelector:
    """Select the most relevant few-shot examples for a given query."""

    def __init__(
        self,
        examples: list[dict[str, str]],
        *,
        strategy: str = "semantic",
        k: int = 3,
    ) -> None:
        self.examples = examples
        self.strategy = strategy
        self.k = k

    def select(self, query: str) -> list[dict[str, str]]:
        """Select *k* examples most relevant to the query."""
        if self.strategy == "random":
            import random
            return random.sample(self.examples, min(self.k, len(self.examples)))

        if self.strategy in ("semantic", "mmr", "bm25"):
            # Simplified: score by word overlap
            query_words = set(query.lower().split())
            scored = []
            for ex in self.examples:
                text = " ".join(ex.values()).lower()
                ex_words = set(text.split())
                overlap = len(query_words & ex_words)
                scored.append((overlap, ex))
            scored.sort(key=lambda x: x[0], reverse=True)
            return [ex for _, ex in scored[: self.k]]

        return self.examples[: self.k]
