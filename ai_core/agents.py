"""
Agentic AI Framework — Enterprise multi-agent orchestration.

Agent types: ReAct, Plan-Execute, Reflexion, Function Call, Structured, Custom
Coordination: sequential, debate, hierarchical, parallel, swarm, supervisor
Features: shared message bus, agent state machine, conflict resolution,
          policy guardrails, cost tracking, consensus voting, dead-letter queue
"""

from __future__ import annotations

import asyncio
import json
import time
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Type
from uuid import uuid4

try:
    from pydantic import BaseModel as _PydanticBaseModel
except ImportError:  # pragma: no cover
    _PydanticBaseModel = None  # type: ignore[assignment,misc]

from ai_core.schemas import AgentResponse, AgentStep, AgentType, TokenUsage, ToolDefinition


# ── Agent State & Message Bus ────────────────────────────────────────────────


class AgentState(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    WAITING = "waiting"
    COMPLETED = "completed"
    FAILED = "failed"
    SUSPENDED = "suspended"


class CoordinationMode(str, Enum):
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    DEBATE = "debate"
    HIERARCHICAL = "hierarchical"
    SWARM = "swarm"
    SUPERVISOR = "supervisor"


@dataclass
class AgentMessage:
    """Message exchanged between agents via the message bus."""
    id: str = field(default_factory=lambda: uuid4().hex[:12])
    sender: str = ""
    recipient: str = ""  # empty = broadcast
    content: str = ""
    msg_type: str = "info"  # info, request, response, error, vote
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    parent_id: str = ""


class MessageBus:
    """In-process message bus for agent-to-agent communication."""

    def __init__(self) -> None:
        self._messages: list[AgentMessage] = []
        self._subscribers: dict[str, list[Callable]] = defaultdict(list)
        self._dead_letters: list[AgentMessage] = []

    def publish(self, message: AgentMessage) -> None:
        self._messages.append(message)
        target = message.recipient or "__broadcast__"
        for handler in self._subscribers.get(target, []):
            try:
                handler(message)
            except Exception:
                self._dead_letters.append(message)
        if target != "__broadcast__":
            for handler in self._subscribers.get("__broadcast__", []):
                try:
                    handler(message)
                except Exception:
                    self._dead_letters.append(message)

    def subscribe(self, agent_name: str, handler: Callable) -> None:
        self._subscribers[agent_name].append(handler)

    def get_history(self, *, sender: str | None = None, recipient: str | None = None) -> list[AgentMessage]:
        msgs = self._messages
        if sender:
            msgs = [m for m in msgs if m.sender == sender]
        if recipient:
            msgs = [m for m in msgs if m.recipient == recipient or m.recipient == ""]
        return msgs

    def get_dead_letters(self) -> list[AgentMessage]:
        return list(self._dead_letters)

    def clear(self) -> None:
        self._messages.clear()
        self._dead_letters.clear()


@dataclass
class ConflictResolution:
    """Tracks how conflicts between agents are resolved."""
    strategy: str = "voting"  # voting, priority, llm_judge
    votes: dict[str, str] = field(default_factory=dict)
    winner: str = ""
    reason: str = ""


# ── Tool Registry ────────────────────────────────────────────────────────────


class Tool:
    """Base class for agent tools."""

    name: str = ""
    description: str = ""
    input_schema: dict[str, Any] = {}

    async def run(self, **kwargs: Any) -> str:
        raise NotImplementedError


class ToolRegistry:
    """Global registry for agent-usable tools."""

    _tools: dict[str, Tool] = {}

    @classmethod
    def register(cls, tool: type[Tool] | Tool) -> type[Tool] | Tool:
        """Register a tool (can be used as decorator)."""
        instance = tool() if isinstance(tool, type) else tool
        cls._tools[instance.name] = instance
        return tool

    @classmethod
    def get(cls, name: str) -> Tool:
        tool = cls._tools.get(name)
        if tool is None:
            raise KeyError(f"Tool not found: {name}")
        return tool

    @classmethod
    def list_tools(cls) -> list[ToolDefinition]:
        return [
            ToolDefinition(
                name=t.name,
                description=t.description,
                input_schema=t.input_schema,
            )
            for t in cls._tools.values()
        ]

    @classmethod
    def clear(cls) -> None:
        cls._tools.clear()


def tool(name: str, description: str = "", input_schema: dict[str, Any] | None = None):
    """Decorator to register a function as a tool."""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        t = Tool()
        t.name = name
        t.description = description or func.__doc__ or ""
        t.input_schema = input_schema or {}
        t.run = func  # type: ignore[assignment]
        ToolRegistry._tools[name] = t
        return func

    return decorator


# ── Base Agent ───────────────────────────────────────────────────────────────


class BaseAgent(ABC):
    """Abstract base for all agent types."""

    def __init__(
        self,
        llm: Any,
        tools: list[Tool] | None = None,
        *,
        max_iterations: int = 10,
        memory: Any = None,
        verbose: bool = False,
    ) -> None:
        self.llm = llm
        self.tools = {t.name: t for t in (tools or [])}
        self.max_iterations = max_iterations
        self.memory = memory
        self.verbose = verbose

    @abstractmethod
    async def run(self, query: str, **kwargs: Any) -> AgentResponse:
        ...

    async def _call_tool(self, name: str, args: dict[str, Any]) -> str:
        tool = self.tools.get(name)
        if tool is None:
            return f"Error: Tool '{name}' not found."
        try:
            result = await tool.run(**args)
            return str(result)
        except Exception as e:
            return f"Error calling {name}: {e}"

    def _tool_descriptions(self) -> str:
        lines: list[str] = []
        for t in self.tools.values():
            lines.append(f"- {t.name}: {t.description}")
        return "\n".join(lines)

    def _tool_schemas(self) -> list[dict[str, Any]]:
        """Return tools in OpenAI function-calling schema format."""
        return [
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.input_schema if t.input_schema else {"type": "object", "properties": {}},
                },
            }
            for t in self.tools.values()
        ]

    async def _call_llm_with_retry(
        self,
        prompt_or_messages: str | list[dict[str, Any]],
        *,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        **kwargs: Any,
    ) -> Any:
        """Call LLM with exponential-backoff retry on transient failures."""
        last_exc: Exception | None = None
        for attempt in range(max_retries):
            try:
                if isinstance(prompt_or_messages, str):
                    return await self.llm.generate(prompt_or_messages, **kwargs)
                return await self.llm.chat(prompt_or_messages, **kwargs)
            except Exception as exc:
                last_exc = exc
                if attempt < max_retries - 1:
                    await asyncio.sleep(initial_delay * (2 ** attempt))
        raise last_exc  # type: ignore[misc]


# ── Agent Implementations ────────────────────────────────────────────────────


class ReActAgent(BaseAgent):
    """ReAct (Reason + Act) agent with thought-action-observation loop."""

    async def run(self, query: str, **kwargs: Any) -> AgentResponse:
        system = (
            f"You are a ReAct agent. You have access to these tools:\n"
            f"{self._tool_descriptions()}\n\n"
            "Use this format:\n"
            "Thought: <reasoning>\n"
            "Action: <tool_name>\n"
            "Action Input: <json_input>\n"
            "Observation: <tool_result>\n"
            "... (repeat)\n"
            "Final Answer: <answer>"
        )
        messages = [{"role": "system", "content": system}, {"role": "user", "content": query}]
        steps: list[AgentStep] = []
        total_tokens = TokenUsage()

        for _ in range(self.max_iterations):
            resp = await self.llm.chat(messages)
            total_tokens.input += resp.usage.input
            total_tokens.output += resp.usage.output
            total_tokens.total += resp.usage.total
            text = resp.text

            if "Final Answer:" in text:
                answer = text.split("Final Answer:")[-1].strip()
                return AgentResponse(
                    output=answer,
                    steps=steps,
                    tokens_used=total_tokens,
                )

            # Parse thought/action
            step = AgentStep()
            if "Thought:" in text:
                step.thought = text.split("Thought:")[-1].split("Action:")[0].strip()
            if "Action:" in text:
                step.action = text.split("Action:")[-1].split("Action Input:")[0].strip()
            if "Action Input:" in text:
                raw_input = text.split("Action Input:")[-1].split("Observation:")[0].strip()
                try:
                    step.action_input = json.loads(raw_input)
                except json.JSONDecodeError:
                    step.action_input = {"input": raw_input}

            if step.action:
                observation = await self._call_tool(step.action, step.action_input)
                step.observation = observation
                messages.append({"role": "assistant", "content": text})
                messages.append({"role": "user", "content": f"Observation: {observation}"})

            steps.append(step)

        return AgentResponse(output="Max iterations reached.", steps=steps, tokens_used=total_tokens)


class PlanExecuteAgent(BaseAgent):
    """Plan-and-Execute agent: plan first, then execute step by step."""

    async def run(self, query: str, **kwargs: Any) -> AgentResponse:
        # Phase 1: Plan
        plan_prompt = (
            f"Create a step-by-step plan to answer this question using available tools.\n"
            f"Tools: {self._tool_descriptions()}\n\n"
            f"Question: {query}\n\nPlan (numbered steps):"
        )
        plan_resp = await self.llm.generate(plan_prompt)
        plan_steps = [
            s.strip()
            for s in plan_resp.text.strip().split("\n")
            if s.strip() and s.strip()[0].isdigit()
        ]

        # Phase 2: Execute
        steps: list[AgentStep] = []
        context = ""
        total_tokens = TokenUsage(
            input=plan_resp.usage.input,
            output=plan_resp.usage.output,
            total=plan_resp.usage.total,
        )

        for plan_step in plan_steps[: self.max_iterations]:
            exec_prompt = (
                f"Execute this step: {plan_step}\n"
                f"Previous context: {context}\n"
                f"Available tools: {self._tool_descriptions()}\n"
                "Respond with Action: <tool> and Action Input: <json>, or answer directly."
            )
            exec_resp = await self.llm.generate(exec_prompt)
            total_tokens.input += exec_resp.usage.input
            total_tokens.output += exec_resp.usage.output
            total_tokens.total += exec_resp.usage.total

            step = AgentStep(thought=plan_step)
            if "Action:" in exec_resp.text:
                step.action = exec_resp.text.split("Action:")[-1].split("Action Input:")[0].strip()
                raw = exec_resp.text.split("Action Input:")[-1].strip()
                try:
                    step.action_input = json.loads(raw)
                except json.JSONDecodeError:
                    step.action_input = {"input": raw}
                step.observation = await self._call_tool(step.action, step.action_input)
                context += f"\n{plan_step}: {step.observation}"
            else:
                step.observation = exec_resp.text
                context += f"\n{plan_step}: {exec_resp.text}"

            steps.append(step)

        # Final synthesis
        final_resp = await self.llm.generate(
            f"Based on these results, provide a final answer:\n{context}\n\nQuestion: {query}"
        )
        total_tokens.input += final_resp.usage.input
        total_tokens.output += final_resp.usage.output
        total_tokens.total += final_resp.usage.total

        return AgentResponse(output=final_resp.text, steps=steps, tokens_used=total_tokens)


class ReflexionAgent(BaseAgent):
    """Reflexion agent: answer, reflect, correct."""

    async def run(self, query: str, **kwargs: Any) -> AgentResponse:
        steps: list[AgentStep] = []
        total_tokens = TokenUsage()

        # Initial answer
        resp = await self.llm.generate(f"Answer the following:\n{query}")
        total_tokens.input += resp.usage.input
        total_tokens.output += resp.usage.output
        total_tokens.total += resp.usage.total
        initial = resp.text
        steps.append(AgentStep(thought="Initial answer", observation=initial))

        # Reflection
        reflect_resp = await self.llm.generate(
            f"Reflect on this answer and identify any errors or improvements:\n\n"
            f"Question: {query}\nAnswer: {initial}\n\nReflection:"
        )
        total_tokens.input += reflect_resp.usage.input
        total_tokens.output += reflect_resp.usage.output
        total_tokens.total += reflect_resp.usage.total
        steps.append(AgentStep(thought="Reflection", observation=reflect_resp.text))

        # Corrected answer
        final_resp = await self.llm.generate(
            f"Based on the reflection, provide a corrected final answer.\n\n"
            f"Question: {query}\nInitial: {initial}\nReflection: {reflect_resp.text}\n\nFinal Answer:"
        )
        total_tokens.input += final_resp.usage.input
        total_tokens.output += final_resp.usage.output
        total_tokens.total += final_resp.usage.total
        steps.append(AgentStep(thought="Final corrected answer", observation=final_resp.text))

        return AgentResponse(output=final_resp.text, steps=steps, tokens_used=total_tokens)


class FunctionCallAgent(BaseAgent):
    """Function-calling agent using OpenAI-style structured tool-use API."""

    async def run(self, query: str, **kwargs: Any) -> AgentResponse:
        schemas = self._tool_schemas()
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": "You are a helpful assistant. Use the provided tools when needed."},
            {"role": "user", "content": query},
        ]

        steps: list[AgentStep] = []
        total_tokens = TokenUsage()
        all_tool_calls: list[dict[str, Any]] = []

        for _ in range(self.max_iterations):
            # Pass tool schemas to the LLM; fall back gracefully if unsupported
            try:
                resp = await self.llm.chat(messages, tools=schemas, tool_choice="auto")
            except TypeError:
                resp = await self.llm.chat(messages)

            total_tokens.input += resp.usage.input
            total_tokens.output += resp.usage.output
            total_tokens.total += resp.usage.total

            # --- Structured tool_calls path ---
            if resp.tool_calls:
                for tc in resp.tool_calls:
                    tool_name = tc.get("name") or tc.get("function", {}).get("name", "")
                    raw_args = tc.get("arguments") or tc.get("function", {}).get("arguments", "{}")
                    try:
                        tool_args: dict[str, Any] = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
                    except json.JSONDecodeError:
                        tool_args = {"input": raw_args}

                    step = AgentStep(action=tool_name, action_input=tool_args)
                    observation = await self._call_tool(tool_name, tool_args)
                    step.observation = observation
                    steps.append(step)
                    all_tool_calls.append({"tool": tool_name, "args": tool_args, "result": observation})

                    messages.append({"role": "assistant", "content": resp.text or "", "tool_calls": resp.tool_calls})
                    messages.append({"role": "tool", "content": observation, "tool_call_id": tc.get("id", "")})
                continue

            # --- Text-fallback path (LLMs that don't emit structured tool_calls) ---
            text = resp.text
            matched = False
            for tool_name in self.tools:
                if tool_name in text:
                    try:
                        after = text.split(tool_name, 1)[1]
                        tool_args = json.loads(after[after.find("{"):after.find("}") + 1])
                    except (json.JSONDecodeError, ValueError):
                        tool_args = {}
                    step = AgentStep(action=tool_name, action_input=tool_args)
                    observation = await self._call_tool(tool_name, tool_args)
                    step.observation = observation
                    steps.append(step)
                    all_tool_calls.append({"tool": tool_name, "args": tool_args, "result": observation})
                    messages.append({"role": "assistant", "content": text})
                    messages.append({"role": "user", "content": f"Tool result: {observation}"})
                    matched = True
                    break

            if not matched:
                return AgentResponse(
                    output=text,
                    steps=steps,
                    tokens_used=total_tokens,
                    tool_calls=all_tool_calls,
                )

        return AgentResponse(output="Max iterations reached.", steps=steps, tokens_used=total_tokens, tool_calls=all_tool_calls)


class StructuredOutputAgent(BaseAgent):
    """Agent that always returns structured (JSON) output, with optional Pydantic validation."""

    async def run(self, query: str, **kwargs: Any) -> AgentResponse:
        output_schema = kwargs.get("output_schema", {"answer": "string", "confidence": "float"})

        # Build schema description for the prompt
        is_pydantic = (
            _PydanticBaseModel is not None
            and isinstance(output_schema, type)
            and issubclass(output_schema, _PydanticBaseModel)
        )
        if is_pydantic:
            schema_str = json.dumps(output_schema.model_json_schema(), indent=2)
        else:
            schema_str = json.dumps(output_schema, indent=2)

        prompt = (
            f"Answer the following and respond ONLY with valid JSON matching this schema:\n"
            f"{schema_str}\n\n{query}"
        )
        resp = await self.llm.generate(prompt)
        raw_text = resp.text

        # Attempt to extract JSON from the response
        try:
            # Strip markdown fences if present
            text = raw_text.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
            parsed = json.loads(text)
        except (json.JSONDecodeError, ValueError):
            parsed = None

        # Validate against Pydantic model if provided
        validated_output = raw_text
        if is_pydantic and parsed is not None:
            try:
                model_instance = output_schema(**parsed)  # type: ignore[operator]
                validated_output = model_instance.model_dump_json()
            except Exception:
                validated_output = raw_text  # return raw if validation fails
        elif parsed is not None:
            validated_output = json.dumps(parsed)

        return AgentResponse(
            output=validated_output,
            tokens_used=TokenUsage(
                input=resp.usage.input,
                output=resp.usage.output,
                total=resp.usage.total,
            ),
        )


# ── Multi-Agent System ───────────────────────────────────────────────────────


class AgentRole:
    """Definition of a role within a multi-agent system."""

    def __init__(
        self,
        name: str,
        agent: BaseAgent,
        *,
        role_description: str = "",
        priority: int = 0,
        domain: str = "",
        max_retries: int = 2,
    ) -> None:
        self.name = name
        self.agent = agent
        self.role_description = role_description
        self.priority = priority
        self.domain = domain
        self.max_retries = max_retries
        self.state = AgentState.IDLE
        self._inbox: list[AgentMessage] = []


@dataclass
class OrchestrationResult:
    """Extended result from multi-agent orchestration."""
    output: str = ""
    agent_outputs: dict[str, str] = field(default_factory=dict)
    steps: list[AgentStep] = field(default_factory=list)
    tokens_used: TokenUsage = field(default_factory=TokenUsage)
    coordination_mode: str = ""
    conflict_resolution: ConflictResolution | None = None
    messages_exchanged: int = 0
    elapsed_seconds: float = 0.0
    cost_usd: float = 0.0
    consensus: str = ""                              # populated by DEBATE mode
    metadata: dict[str, Any] = field(default_factory=dict)  # mode-specific info

    # ── Convenience aliases ──────────────────────────────────
    @property
    def results(self) -> dict[str, str]:
        """Alias for agent_outputs — matches docs/UI usage."""
        return self.agent_outputs

    @property
    def final_answer(self) -> str:
        """Alias for output — matches docs/UI usage."""
        return self.output

    @property
    def cost(self) -> float:
        """Alias for cost_usd — matches docs/UI usage."""
        return self.cost_usd


class MultiAgentSystem:
    """Enterprise-grade multi-agent orchestration with coordination strategies.

    Supports: sequential, parallel, debate (with voting), hierarchical,
    swarm (dynamic routing), and supervisor (with policy guardrails).
    """

    def __init__(
        self,
        agents: list[AgentRole],
        *,
        coordination: str | CoordinationMode = "sequential",
        mode: str | CoordinationMode | None = None,  # alias for coordination
        message_bus: MessageBus | None = None,
        max_rounds: int = 3,
        rounds: int | None = None,  # alias for max_rounds
        cost_limit_usd: float | None = None,
        policy_check: Callable[[str, dict[str, Any]], bool] | None = None,
    ) -> None:
        # Accept alias params
        if mode is not None:
            coordination = mode
        if rounds is not None:
            max_rounds = rounds
        self.agents = {a.name: a for a in agents}
        self.coordination = CoordinationMode(coordination) if isinstance(coordination, str) else coordination
        self.bus = message_bus or MessageBus()
        self.max_rounds = max_rounds
        self.cost_limit_usd = cost_limit_usd
        self._policy_check = policy_check
        self._run_log: list[dict[str, Any]] = []

        # Wire agents to the bus
        for role in self.agents.values():
            self.bus.subscribe(role.name, lambda msg, r=role: r._inbox.append(msg))

    async def run(self, query: str, **kwargs: Any) -> OrchestrationResult:
        start = time.time()
        mode = self.coordination

        # Policy guard
        if self._policy_check and not self._policy_check(query, kwargs):
            return OrchestrationResult(
                output="Query blocked by policy guard.",
                coordination_mode=mode.value,
            )

        if mode == CoordinationMode.SEQUENTIAL:
            result = await self._run_sequential(query, **kwargs)
        elif mode == CoordinationMode.PARALLEL:
            result = await self._run_parallel(query, **kwargs)
        elif mode == CoordinationMode.DEBATE:
            result = await self._run_debate(query, **kwargs)
        elif mode == CoordinationMode.HIERARCHICAL:
            result = await self._run_hierarchical(query, **kwargs)
        elif mode == CoordinationMode.SWARM:
            result = await self._run_swarm(query, **kwargs)
        elif mode == CoordinationMode.SUPERVISOR:
            result = await self._run_supervisor(query, **kwargs)
        else:
            result = await self._run_sequential(query, **kwargs)

        result.elapsed_seconds = round(time.time() - start, 3)
        result.coordination_mode = mode.value
        result.messages_exchanged = len(self.bus.get_history())
        self._run_log.append({
            "query": query,
            "mode": mode.value,
            "elapsed": result.elapsed_seconds,
            "agents_used": list(result.agent_outputs.keys()),
        })
        return result

    def _accumulate_tokens(self, total: TokenUsage, resp: AgentResponse) -> None:
        total.input += resp.tokens_used.input
        total.output += resp.tokens_used.output
        total.total += resp.tokens_used.total

    async def _run_sequential(self, query: str, **kwargs: Any) -> OrchestrationResult:
        context = query
        all_steps: list[AgentStep] = []
        total_tokens = TokenUsage()
        agent_outputs: dict[str, str] = {}

        for role in self.agents.values():
            role.state = AgentState.RUNNING
            resp = await role.agent.run(context, **kwargs)
            role.state = AgentState.COMPLETED
            all_steps.extend(resp.steps)
            self._accumulate_tokens(total_tokens, resp)
            agent_outputs[role.name] = resp.output

            self.bus.publish(AgentMessage(
                sender=role.name, content=resp.output, msg_type="response",
            ))
            context = f"Previous agent ({role.name}) said: {resp.output}\n\nOriginal query: {query}"

        last = list(agent_outputs.values())[-1] if agent_outputs else ""
        return OrchestrationResult(
            output=last,
            agent_outputs=agent_outputs,
            steps=all_steps,
            tokens_used=total_tokens,
            metadata={"stages_completed": list(agent_outputs.keys())},
        )

    async def _run_parallel(self, query: str, **kwargs: Any) -> OrchestrationResult:
        """Run all agents in parallel and merge results."""
        all_steps: list[AgentStep] = []
        total_tokens = TokenUsage()
        agent_outputs: dict[str, str] = {}

        async def _run_one(role: AgentRole) -> tuple[str, AgentResponse]:
            role.state = AgentState.RUNNING
            resp = await role.agent.run(query, **kwargs)
            role.state = AgentState.COMPLETED
            return role.name, resp

        tasks = [_run_one(role) for role in self.agents.values()]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for item in results:
            if isinstance(item, Exception):
                continue
            name, resp = item
            all_steps.extend(resp.steps)
            self._accumulate_tokens(total_tokens, resp)
            agent_outputs[name] = resp.output
            self.bus.publish(AgentMessage(sender=name, content=resp.output, msg_type="response"))

        # Merge: concatenate parallel outputs
        merged = "\n\n".join(f"[{name}]: {out}" for name, out in agent_outputs.items())
        return OrchestrationResult(
            output=merged, agent_outputs=agent_outputs, steps=all_steps, tokens_used=total_tokens,
        )

    async def _run_debate(self, query: str, **kwargs: Any) -> OrchestrationResult:
        """Multi-round debate with consensus voting."""
        all_steps: list[AgentStep] = []
        total_tokens = TokenUsage()
        agent_outputs: dict[str, str] = {}

        # Round 1: Independent answers
        for role in self.agents.values():
            role.state = AgentState.RUNNING
            resp = await role.agent.run(query, **kwargs)
            role.state = AgentState.COMPLETED
            agent_outputs[role.name] = resp.output
            all_steps.extend(resp.steps)
            self._accumulate_tokens(total_tokens, resp)

        # Rounds 2..N: Challenge and refine
        for round_num in range(1, self.max_rounds):
            debate_context = "\n".join(
                f"{name}: {answer}" for name, answer in agent_outputs.items()
            )
            new_outputs: dict[str, str] = {}
            for role in self.agents.values():
                challenge = (
                    f"Round {round_num + 1} debate. Other agents said:\n{debate_context}\n\n"
                    f"Original question: {query}\n"
                    f"Your previous answer: {agent_outputs[role.name]}\n"
                    f"Refine your answer or defend your position:"
                )
                resp = await role.agent.run(challenge, **kwargs)
                new_outputs[role.name] = resp.output
                all_steps.extend(resp.steps)
                self._accumulate_tokens(total_tokens, resp)
                self.bus.publish(AgentMessage(
                    sender=role.name, content=resp.output,
                    msg_type="vote", metadata={"round": round_num + 1},
                ))
            agent_outputs = new_outputs

        # Consensus: first agent synthesizes
        first_agent = next(iter(self.agents.values()))
        summary = "\n".join(f"{n}: {a}" for n, a in agent_outputs.items())
        synthesis = await first_agent.agent.run(
            f"Synthesize these final positions into one authoritative answer:\n\n{summary}",
            **kwargs,
        )
        self._accumulate_tokens(total_tokens, synthesis)

        conflict = ConflictResolution(
            strategy="debate_consensus",
            votes=agent_outputs,
            winner=first_agent.name,
            reason="Synthesized after multi-round debate",
        )

        return OrchestrationResult(
            output=synthesis.output,
            consensus=synthesis.output,
            agent_outputs=agent_outputs,
            steps=all_steps,
            tokens_used=total_tokens,
            conflict_resolution=conflict,
            metadata={
                "rounds_completed": self.max_rounds,
                "agents": list(agent_outputs.keys()),
                "synthesizer": first_agent.name,
            },
        )

    async def _run_hierarchical(self, query: str, **kwargs: Any) -> OrchestrationResult:
        """Manager-worker pattern: first agent delegates, workers execute, manager synthesizes."""
        agent_list = list(self.agents.values())
        if len(agent_list) < 2:
            return await self._run_sequential(query, **kwargs)

        manager = agent_list[0]
        workers = agent_list[1:]

        manager.state = AgentState.RUNNING
        manager_resp = await manager.agent.run(
            f"You are a manager agent. Break down this task and delegate sub-tasks to workers:\n"
            f"{query}\n\nAvailable workers: {', '.join(w.name + ' (' + w.role_description + ')' for w in workers)}",
            **kwargs,
        )
        manager.state = AgentState.COMPLETED

        all_steps = list(manager_resp.steps)
        total_tokens = TokenUsage(
            input=manager_resp.tokens_used.input,
            output=manager_resp.tokens_used.output,
            total=manager_resp.tokens_used.total,
        )
        agent_outputs: dict[str, str] = {manager.name: manager_resp.output}

        worker_results: list[str] = []
        for worker in workers:
            worker.state = AgentState.RUNNING
            self.bus.publish(AgentMessage(
                sender=manager.name, recipient=worker.name,
                content=manager_resp.output, msg_type="request",
            ))
            resp = await worker.agent.run(
                f"The manager assigned you this task: {manager_resp.output}\n"
                f"Your role: {worker.role_description}\nOriginal question: {query}",
                **kwargs,
            )
            worker.state = AgentState.COMPLETED
            worker_results.append(f"{worker.name}: {resp.output}")
            agent_outputs[worker.name] = resp.output
            all_steps.extend(resp.steps)
            self._accumulate_tokens(total_tokens, resp)

        # Manager synthesizes
        final = await manager.agent.run(
            f"Synthesize these worker results into a final answer:\n"
            + "\n".join(worker_results) + f"\n\nOriginal: {query}",
            **kwargs,
        )
        self._accumulate_tokens(total_tokens, final)
        agent_outputs[f"{manager.name}_final"] = final.output

        return OrchestrationResult(
            output=final.output,
            agent_outputs=agent_outputs,
            steps=all_steps,
            tokens_used=total_tokens,
            metadata={
                "stages_completed": list(agent_outputs.keys()),
                "manager": manager.name,
                "workers": [w.name for w in workers],
            },
        )

    async def _run_swarm(self, query: str, **kwargs: Any) -> OrchestrationResult:
        """Dynamic routing: route query to the best-matching agent by domain."""
        all_steps: list[AgentStep] = []
        total_tokens = TokenUsage()
        agent_outputs: dict[str, str] = {}

        # Route based on domain keywords in query
        query_lower = query.lower()
        matched_agents = []
        for role in self.agents.values():
            if role.domain and role.domain.lower() in query_lower:
                matched_agents.append(role)

        # Fallback: use all agents if no domain match
        if not matched_agents:
            matched_agents = list(self.agents.values())

        # Sort by priority (higher first)
        matched_agents.sort(key=lambda r: r.priority, reverse=True)

        for role in matched_agents:
            role.state = AgentState.RUNNING
            resp = await role.agent.run(query, **kwargs)
            role.state = AgentState.COMPLETED
            agent_outputs[role.name] = resp.output
            all_steps.extend(resp.steps)
            self._accumulate_tokens(total_tokens, resp)

            # If first high-priority agent gives confident answer, stop
            if role.priority > 0 and resp.output:
                break

        last = list(agent_outputs.values())[-1] if agent_outputs else ""
        return OrchestrationResult(
            output=last,
            agent_outputs=agent_outputs,
            steps=all_steps,
            tokens_used=total_tokens,
            metadata={
                "agents_activated": list(agent_outputs.keys()),
                "routing": "domain_match" if any(r.domain for r in matched_agents) else "all",
            },
        )

    async def _run_supervisor(self, query: str, **kwargs: Any) -> OrchestrationResult:
        """Supervisor pattern: a dedicated supervisor agent decides routing and validates outputs."""
        agent_list = list(self.agents.values())
        if len(agent_list) < 2:
            return await self._run_sequential(query, **kwargs)

        supervisor = agent_list[0]
        workers = {w.name: w for w in agent_list[1:]}
        all_steps: list[AgentStep] = []
        total_tokens = TokenUsage()
        agent_outputs: dict[str, str] = {}

        for _round in range(self.max_rounds):
            # Supervisor decides which worker to call
            worker_desc = "\n".join(
                f"- {w.name}: {w.role_description}" for w in workers.values()
            )
            supervisor.state = AgentState.RUNNING
            decision = await supervisor.agent.run(
                f"You are a supervisor. Given this query, decide which worker to call next.\n"
                f"Query: {query}\n"
                f"Previous results: {json.dumps(agent_outputs) if agent_outputs else 'None'}\n"
                f"Workers:\n{worker_desc}\n\n"
                f"Respond with: CALL <worker_name> or DONE <final_answer>",
                **kwargs,
            )
            supervisor.state = AgentState.COMPLETED
            all_steps.extend(decision.steps)
            self._accumulate_tokens(total_tokens, decision)

            text = decision.output.strip()
            if text.upper().startswith("DONE"):
                final_answer = text[4:].strip()
                return OrchestrationResult(
                    output=final_answer,
                    agent_outputs=agent_outputs,
                    steps=all_steps,
                    tokens_used=total_tokens,
                    metadata={
                        "stages_completed": list(agent_outputs.keys()),
                        "supervisor": supervisor.name,
                        "rounds_completed": _round + 1,
                    },
                )

            # Parse CALL <worker>
            called_worker = None
            if text.upper().startswith("CALL"):
                worker_name = text[4:].strip().split()[0] if len(text) > 4 else ""
                called_worker = workers.get(worker_name)

            if called_worker is None:
                called_worker = next(iter(workers.values()))

            called_worker.state = AgentState.RUNNING
            resp = await called_worker.agent.run(query, **kwargs)
            called_worker.state = AgentState.COMPLETED
            agent_outputs[called_worker.name] = resp.output
            all_steps.extend(resp.steps)
            self._accumulate_tokens(total_tokens, resp)

        # Fallback synthesis
        merged = "\n".join(f"{n}: {o}" for n, o in agent_outputs.items())
        return OrchestrationResult(
            output=merged,
            agent_outputs=agent_outputs,
            steps=all_steps,
            tokens_used=total_tokens,
            metadata={
                "stages_completed": list(agent_outputs.keys()),
                "supervisor": agent_list[0].name,
                "rounds_completed": _round + 1,
            },
        )

    def get_run_log(self) -> list[dict[str, Any]]:
        return list(self._run_log)

    def get_agent_states(self) -> dict[str, str]:
        return {name: role.state.value for name, role in self.agents.items()}


# ── Agent Factory ────────────────────────────────────────────────────────────

_AGENT_REGISTRY: dict[AgentType, type[BaseAgent]] = {
    AgentType.REACT: ReActAgent,
    AgentType.PLAN_EXECUTE: PlanExecuteAgent,
    AgentType.REFLEXION: ReflexionAgent,
    AgentType.FUNCTION_CALL: FunctionCallAgent,
    AgentType.STRUCTURED: StructuredOutputAgent,
}


class AgentExecutor:
    """Create and execute agents by type."""

    @staticmethod
    def create(
        agent_type: str | AgentType,
        llm: Any,
        tools: list[Tool] | None = None,
        *,
        max_iterations: int = 10,
        memory: Any = None,
        verbose: bool = False,
    ) -> BaseAgent:
        at = AgentType(agent_type)
        cls = _AGENT_REGISTRY.get(at)
        if cls is None:
            raise ValueError(f"Unknown agent type: {at}")
        return cls(llm, tools, max_iterations=max_iterations, memory=memory, verbose=verbose)


# ── Enterprise Pipeline Builder ──────────────────────────────────────────────


class AgentPipelineBuilder:
    """Fluent builder for constructing multi-agent orchestration pipelines."""

    def __init__(self) -> None:
        self._roles: list[AgentRole] = []
        self._coordination: CoordinationMode = CoordinationMode.SEQUENTIAL
        self._max_rounds: int = 3
        self._cost_limit: float | None = None
        self._policy_check: Callable | None = None
        self._bus: MessageBus | None = None

    def add_agent(
        self,
        name: str,
        agent: BaseAgent,
        *,
        role_description: str = "",
        priority: int = 0,
        domain: str = "",
    ) -> AgentPipelineBuilder:
        self._roles.append(AgentRole(
            name=name, agent=agent,
            role_description=role_description, priority=priority, domain=domain,
        ))
        return self

    def add_stage(
        self,
        name: str,
        agent: BaseAgent,
        *,
        role_description: str = "",
        priority: int = 0,
        domain: str = "",
    ) -> AgentPipelineBuilder:
        """Alias for add_agent — pipeline-stage oriented naming."""
        return self.add_agent(name, agent, role_description=role_description, priority=priority, domain=domain)

    def with_coordination(self, mode: str | CoordinationMode) -> AgentPipelineBuilder:
        self._coordination = CoordinationMode(mode) if isinstance(mode, str) else mode
        return self

    def with_mode(self, mode: str | CoordinationMode) -> AgentPipelineBuilder:
        """Alias for with_coordination."""
        return self.with_coordination(mode)

    def with_max_rounds(self, rounds: int) -> AgentPipelineBuilder:
        self._max_rounds = rounds
        return self

    def with_cost_limit(self, limit_usd: float) -> AgentPipelineBuilder:
        self._cost_limit = limit_usd
        return self

    def with_policy_check(self, check: Callable) -> AgentPipelineBuilder:
        self._policy_check = check
        return self

    def with_message_bus(self, bus: MessageBus) -> AgentPipelineBuilder:
        self._bus = bus
        return self

    def build(self) -> MultiAgentSystem:
        return MultiAgentSystem(
            self._roles,
            coordination=self._coordination,
            message_bus=self._bus,
            max_rounds=self._max_rounds,
            cost_limit_usd=self._cost_limit,
            policy_check=self._policy_check,
        )
