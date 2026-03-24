"""
Evaluation Suite — Multi-framework evaluation for RAG pipelines.

Metrics: faithfulness, answer_relevancy, context_recall, context_precision,
         harmfulness, hallucination
Frameworks: RAGAS, DeepEval, TruLens, UpTrain, Custom
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from ai_core.schemas import EvalMetric, EvalReport


class BaseEvaluator(ABC):
    """Abstract base for evaluation frameworks."""

    @abstractmethod
    async def evaluate(
        self,
        questions: list[str],
        answers: list[str],
        contexts: list[list[str]],
        *,
        ground_truth: list[str] | None = None,
    ) -> EvalReport:
        ...


class RAGEvaluator(BaseEvaluator):
    """Built-in RAG evaluation with common metrics."""

    def __init__(
        self,
        metrics: list[str] | None = None,
        llm: Any = None,
    ) -> None:
        self.metrics = metrics or [
            "faithfulness",
            "answer_relevancy",
            "context_recall",
            "context_precision",
        ]
        self.llm = llm

    async def evaluate(
        self,
        questions: list[str],
        answers: list[str],
        contexts: list[list[str]],
        *,
        ground_truth: list[str] | None = None,
    ) -> EvalReport:
        results: list[EvalMetric] = []

        for metric_name in self.metrics:
            scores: list[float] = []
            for i in range(len(questions)):
                score = await self._compute_metric(
                    metric_name,
                    question=questions[i],
                    answer=answers[i],
                    context=contexts[i] if i < len(contexts) else [],
                    ground_truth=ground_truth[i] if ground_truth and i < len(ground_truth) else None,
                )
                scores.append(score)

            avg_score = sum(scores) / len(scores) if scores else 0.0
            results.append(
                EvalMetric(
                    name=metric_name,
                    score=avg_score,
                    details={"per_question": scores},
                )
            )

        return EvalReport(metrics=results)

    async def _compute_metric(
        self,
        metric: str,
        *,
        question: str,
        answer: str,
        context: list[str],
        ground_truth: str | None,
    ) -> float:
        if metric == "faithfulness":
            return self._faithfulness(answer, context)
        if metric == "answer_relevancy":
            return self._answer_relevancy(question, answer)
        if metric == "context_recall":
            return self._context_recall(answer, context, ground_truth)
        if metric == "context_precision":
            return self._context_precision(question, context)
        if metric == "harmfulness":
            return self._harmfulness(answer)
        if metric == "hallucination":
            return self._hallucination(answer, context)
        return 0.0

    @staticmethod
    def _faithfulness(answer: str, context: list[str]) -> float:
        """Check if answer claims are supported by context (word overlap proxy)."""
        if not context:
            return 0.0
        answer_words = set(answer.lower().split())
        context_text = " ".join(context).lower()
        context_words = set(context_text.split())
        if not answer_words:
            return 1.0
        overlap = len(answer_words & context_words)
        return min(overlap / len(answer_words), 1.0)

    @staticmethod
    def _answer_relevancy(question: str, answer: str) -> float:
        """Check if answer addresses the question."""
        q_words = set(question.lower().split())
        a_words = set(answer.lower().split())
        if not q_words:
            return 1.0
        overlap = len(q_words & a_words)
        return min(overlap / len(q_words) * 2, 1.0)

    @staticmethod
    def _context_recall(answer: str, context: list[str], ground_truth: str | None) -> float:
        """How much of the ground truth is captured by context."""
        if not ground_truth:
            return 0.5  # No ground truth → neutral
        gt_words = set(ground_truth.lower().split())
        ctx_words = set(" ".join(context).lower().split())
        if not gt_words:
            return 1.0
        return len(gt_words & ctx_words) / len(gt_words)

    @staticmethod
    def _context_precision(question: str, context: list[str]) -> float:
        """How relevant are the retrieved contexts to the question."""
        if not context:
            return 0.0
        q_words = set(question.lower().split())
        scores: list[float] = []
        for ctx in context:
            ctx_words = set(ctx.lower().split())
            if ctx_words:
                scores.append(len(q_words & ctx_words) / len(ctx_words))
            else:
                scores.append(0.0)
        return sum(scores) / len(scores) if scores else 0.0

    @staticmethod
    def _harmfulness(answer: str) -> float:
        """Basic harmfulness check (inverse: higher = less harmful = better)."""
        harmful_patterns = [
            "kill", "harm", "attack", "illegal", "weapon",
            "hack", "exploit", "steal", "destroy",
        ]
        text_lower = answer.lower()
        matches = sum(1 for p in harmful_patterns if p in text_lower)
        return max(1.0 - matches * 0.2, 0.0)

    @staticmethod
    def _hallucination(answer: str, context: list[str]) -> float:
        """Inverse hallucination score (higher = less hallucination = better)."""
        if not context:
            return 0.0
        answer_words = set(answer.lower().split()) - {"the", "a", "an", "is", "are", "was", "were", "in", "on", "at", "to", "for", "of", "and", "or"}
        ctx_words = set(" ".join(context).lower().split())
        if not answer_words:
            return 1.0
        grounded = len(answer_words & ctx_words) / len(answer_words)
        return grounded


class RAGASEvaluator(BaseEvaluator):
    """Wrapper for RAGAS evaluation framework."""

    async def evaluate(
        self,
        questions: list[str],
        answers: list[str],
        contexts: list[list[str]],
        *,
        ground_truth: list[str] | None = None,
    ) -> EvalReport:
        from ragas import evaluate as ragas_evaluate  # type: ignore[import-untyped]
        from ragas.metrics import (  # type: ignore[import-untyped]
            answer_relevancy,
            context_precision,
            context_recall,
            faithfulness,
        )
        from datasets import Dataset  # type: ignore[import-untyped]

        data = {
            "question": questions,
            "answer": answers,
            "contexts": contexts,
        }
        if ground_truth:
            data["ground_truth"] = ground_truth

        dataset = Dataset.from_dict(data)
        result = ragas_evaluate(
            dataset,
            metrics=[faithfulness, answer_relevancy, context_recall, context_precision],
        )
        metrics = [
            EvalMetric(name=k, score=v)
            for k, v in result.items()
            if isinstance(v, (int, float))
        ]
        return EvalReport(metrics=metrics)


class DeepEvalEvaluator(BaseEvaluator):
    """Wrapper for DeepEval framework."""

    async def evaluate(
        self,
        questions: list[str],
        answers: list[str],
        contexts: list[list[str]],
        *,
        ground_truth: list[str] | None = None,
    ) -> EvalReport:
        from deepeval import evaluate as de_evaluate  # type: ignore[import-untyped]
        from deepeval.metrics import (  # type: ignore[import-untyped]
            AnswerRelevancyMetric,
            FaithfulnessMetric,
            HallucinationMetric,
        )
        from deepeval.test_case import LLMTestCase  # type: ignore[import-untyped]

        test_cases = [
            LLMTestCase(
                input=q,
                actual_output=a,
                retrieval_context=c,
                expected_output=ground_truth[i] if ground_truth and i < len(ground_truth) else None,
            )
            for i, (q, a, c) in enumerate(zip(questions, answers, contexts))
        ]
        metrics_list = [FaithfulnessMetric(), AnswerRelevancyMetric(), HallucinationMetric()]
        results = de_evaluate(test_cases, metrics_list)

        eval_metrics = [
            EvalMetric(name=m.__class__.__name__, score=m.score or 0.0)
            for m in metrics_list
        ]
        return EvalReport(metrics=eval_metrics)


# ── Pipeline Evaluator (convenience) ────────────────────────────────────────


class PipelineEvaluator:
    """Evaluate a RAG pipeline end-to-end."""

    def __init__(
        self,
        evaluator: BaseEvaluator | None = None,
    ) -> None:
        self.evaluator = evaluator or RAGEvaluator()

    async def evaluate(
        self,
        questions: list[str],
        pipeline: Any,
        *,
        ground_truth: list[str] | None = None,
    ) -> EvalReport:
        """Run questions through the pipeline and evaluate results."""
        answers: list[str] = []
        contexts: list[list[str]] = []

        for q in questions:
            resp = await pipeline.query(q)
            answers.append(resp.answer)
            contexts.append([s.text for s in resp.sources])

        report = await self.evaluator.evaluate(
            questions, answers, contexts, ground_truth=ground_truth
        )
        return report
