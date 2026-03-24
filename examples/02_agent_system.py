"""
Example 02 — Agent System
==========================
Demonstrates:
- @tool decorator for defining custom tools
- ReActAgent — thought/action/observation loop
- PlanExecuteAgent — plan then execute
- ReflexionAgent — self-correction loop
- MultiAgentSystem — debate coordination mode
- MemoryFactory — conversation buffer memory
- Observability tracing on agent calls

Run:
    python examples/02_agent_system.py
"""

import asyncio
import json
import os
from datetime import datetime

from ai_core.agents import AgentExecutor, MultiAgentSystem, ToolRegistry, tool
from ai_core.llm import LLMFactory
from ai_core.schemas import AgentType
from ai_shared.logging_utils import get_logger, log_execution
from ai_shared.memory import MemoryFactory
from ai_shared.observability import Tracer, metrics, trace
from ai_shared.resilience import CircuitBreaker, retry

logger = get_logger("example.agents")
tracer = Tracer()

# ── Tool Definitions ──────────────────────────────────────────────────────────

@tool
def get_current_time() -> str:
    """Return the current UTC date and time."""
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")


@tool
def calculate(expression: str) -> str:
    """Safely evaluate a mathematical expression and return the result."""
    allowed = set("0123456789+-*/().% ")
    if not all(c in allowed for c in expression):
        return "Error: expression contains disallowed characters."
    try:
        result = eval(expression, {"__builtins__": {}})  # noqa: S307 – guarded above
        return str(result)
    except Exception as exc:
        return f"Error: {exc}"


@tool
def lookup_capital(country: str) -> str:
    """Return the capital city of a given country."""
    capitals = {
        "france": "Paris",
        "germany": "Berlin",
        "japan": "Tokyo",
        "brazil": "Brasília",
        "australia": "Canberra",
        "canada": "Ottawa",
        "india": "New Delhi",
        "usa": "Washington D.C.",
        "united states": "Washington D.C.",
        "china": "Beijing",
        "uk": "London",
        "united kingdom": "London",
    }
    return capitals.get(country.lower(), f"Unknown capital for '{country}'")


@tool
def summarize_text(text: str, max_words: int = 30) -> str:
    """Return a truncated summary of text (first max_words words)."""
    words = text.split()
    summary = " ".join(words[:max_words])
    if len(words) > max_words:
        summary += " …"
    return summary


# ── Resilient LLM factory with circuit breaker ───────────────────────────────

_openai_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=30)


def get_llm(provider: str = "openai", model: str = "gpt-4o-mini"):
    return LLMFactory.create(provider, model)


# ── ReAct Agent ───────────────────────────────────────────────────────────────

async def demo_react_agent() -> None:
    print("\n" + "=" * 60)
    print("ReAct Agent — Thought / Action / Observation Loop")
    print("=" * 60)

    llm = get_llm()
    memory = MemoryFactory.create("buffer", max_turns=10)

    agent = AgentExecutor.create(
        AgentType.REACT,
        llm=llm,
        tools=[get_current_time, calculate, lookup_capital],
        max_iterations=6,
        memory=memory,
        verbose=True,
    )

    questions = [
        "What time is it right now?",
        "What is 1234 * 5678?",
        "What is the capital of Japan?",
    ]

    for question in questions:
        logger.info("ReAct question: %s", question)
        with tracer.trace("react_agent"):
            result = await agent.run(question)
        print(f"\nQ: {question}")
        print(f"A: {result.answer}")
        metrics.increment("agent_react_queries")


# ── PlanExecute Agent ─────────────────────────────────────────────────────────

async def demo_plan_execute_agent() -> None:
    print("\n" + "=" * 60)
    print("PlanExecute Agent — Plan then Execute")
    print("=" * 60)

    llm = get_llm()
    agent = AgentExecutor.create(
        AgentType.PLAN_EXECUTE,
        llm=llm,
        tools=[get_current_time, calculate, lookup_capital, summarize_text],
        max_iterations=8,
        verbose=True,
    )

    task = (
        "Find the capitals of France, Germany, and Japan, "
        "then report the current time."
    )
    logger.info("PlanExecute task: %s", task)

    with tracer.trace("plan_execute_agent"):
        result = await agent.run(task)

    print(f"\nTask : {task}")
    print(f"Plan : {json.dumps(result.plan, indent=2) if hasattr(result, 'plan') else 'N/A'}")
    print(f"Answer: {result.answer}")
    metrics.increment("agent_plan_execute_queries")


# ── Reflexion Agent ───────────────────────────────────────────────────────────

async def demo_reflexion_agent() -> None:
    print("\n" + "=" * 60)
    print("Reflexion Agent — Answer → Reflect → Correct")
    print("=" * 60)

    llm = get_llm()
    agent = AgentExecutor.create(
        AgentType.REFLEXION,
        llm=llm,
        tools=[calculate],
        max_iterations=3,
        verbose=True,
    )

    question = "What is 17 * 23 + (144 / 12)?"
    logger.info("Reflexion question: %s", question)

    with tracer.trace("reflexion_agent"):
        result = await agent.run(question)

    print(f"\nQuestion   : {question}")
    print(f"Answer     : {result.answer}")
    if result.steps:
        print(f"Reflections: {len(result.steps)} step(s)")
    metrics.increment("agent_reflexion_queries")


# ── Multi-Agent System ────────────────────────────────────────────────────────

async def demo_multi_agent() -> None:
    print("\n" + "=" * 60)
    print("Multi-Agent System — Debate Coordination")
    print("=" * 60)

    llm = get_llm()

    # Build two specialist agents
    researcher = AgentExecutor.create(
        AgentType.REACT,
        llm=llm,
        tools=[lookup_capital, get_current_time],
        max_iterations=4,
    )
    analyst = AgentExecutor.create(
        AgentType.PLAN_EXECUTE,
        llm=llm,
        tools=[calculate, summarize_text],
        max_iterations=4,
    )

    multi_system = MultiAgentSystem(
        agents={"researcher": researcher, "analyst": analyst},
        coordination_mode="debate",
    )

    question = "What are the top considerations when choosing a vector database?"
    logger.info("Multi-agent question: %s", question)

    with tracer.trace("multi_agent"):
        result = await multi_system.run(question)

    print(f"\nQuestion: {question}")
    print(f"Answer  : {result.answer}")
    metrics.increment("agent_multi_queries")


# ── Metrics Summary ───────────────────────────────────────────────────────────

def print_metrics() -> None:
    print("\n── Agent Metrics ────────────────────────────────────")
    snap = metrics.snapshot()
    for key, value in snap.get("counters", {}).items():
        if key.startswith("agent_"):
            print(f"  {key}: {value}")


# ── Main ──────────────────────────────────────────────────────────────────────

async def main() -> None:
    if not os.getenv("OPENAI_API_KEY"):
        logger.warning(
            "OPENAI_API_KEY not set — agent demos will show structure only."
        )

    await demo_react_agent()
    await demo_plan_execute_agent()
    await demo_reflexion_agent()
    await demo_multi_agent()
    print_metrics()


if __name__ == "__main__":
    asyncio.run(main())
