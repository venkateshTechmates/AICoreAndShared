"""
Agentic AI Framework — 6 agent types with multi-agent orchestration.

Agent types: ReAct, Plan-Execute, Reflexion, Function Call, Structured, Custom
Coordination: hierarchical, sequential, swarm, debate
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Any, Callable

from ai_core.schemas import AgentResponse, AgentStep, AgentType, TokenUsage, ToolDefinition


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
    """Function-calling agent using structured tool-use API."""

    async def run(self, query: str, **kwargs: Any) -> AgentResponse:
        tool_schemas = [
            {"name": t.name, "description": t.description, "parameters": t.input_schema}
            for t in self.tools.values()
        ]
        messages = [
            {"role": "system", "content": "Use the provided functions to answer the user's question."},
            {"role": "user", "content": query},
        ]

        steps: list[AgentStep] = []
        total_tokens = TokenUsage()

        for _ in range(self.max_iterations):
            resp = await self.llm.chat(messages)
            total_tokens.input += resp.usage.input
            total_tokens.output += resp.usage.output
            total_tokens.total += resp.usage.total

            # Simple heuristic: check if response calls a tool
            text = resp.text
            has_tool_call = any(t.name in text for t in self.tools.values())

            if not has_tool_call:
                return AgentResponse(output=text, steps=steps, tokens_used=total_tokens)

            for tool_name, tool_obj in self.tools.items():
                if tool_name in text:
                    step = AgentStep(action=tool_name)
                    observation = await self._call_tool(tool_name, {})
                    step.observation = observation
                    steps.append(step)
                    messages.append({"role": "assistant", "content": text})
                    messages.append({"role": "user", "content": f"Tool result: {observation}"})
                    break

        return AgentResponse(output="Max iterations reached.", steps=steps, tokens_used=total_tokens)


class StructuredOutputAgent(BaseAgent):
    """Agent that always returns structured (JSON) output."""

    async def run(self, query: str, **kwargs: Any) -> AgentResponse:
        output_schema = kwargs.get("output_schema", {"answer": "string", "confidence": "float"})
        prompt = (
            f"Answer the following and respond ONLY with valid JSON matching this schema:\n"
            f"{json.dumps(output_schema, indent=2)}\n\n{query}"
        )
        resp = await self.llm.generate(prompt)
        return AgentResponse(
            output=resp.text,
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
    ) -> None:
        self.name = name
        self.agent = agent
        self.role_description = role_description


class MultiAgentSystem:
    """Orchestrate multiple agents with coordination strategies."""

    def __init__(
        self,
        agents: list[AgentRole],
        *,
        coordination: str = "sequential",
    ) -> None:
        self.agents = {a.name: a for a in agents}
        self.coordination = coordination

    async def run(self, query: str, **kwargs: Any) -> AgentResponse:
        if self.coordination == "sequential":
            return await self._run_sequential(query, **kwargs)
        if self.coordination == "debate":
            return await self._run_debate(query, **kwargs)
        if self.coordination == "hierarchical":
            return await self._run_hierarchical(query, **kwargs)
        return await self._run_sequential(query, **kwargs)

    async def _run_sequential(self, query: str, **kwargs: Any) -> AgentResponse:
        context = query
        all_steps: list[AgentStep] = []
        total_tokens = TokenUsage()
        last_output = ""

        for role in self.agents.values():
            resp = await role.agent.run(context, **kwargs)
            all_steps.extend(resp.steps)
            total_tokens.input += resp.tokens_used.input
            total_tokens.output += resp.tokens_used.output
            total_tokens.total += resp.tokens_used.total
            context = f"Previous agent ({role.name}) said: {resp.output}\n\nOriginal query: {query}"
            last_output = resp.output

        return AgentResponse(output=last_output, steps=all_steps, tokens_used=total_tokens)

    async def _run_debate(self, query: str, **kwargs: Any) -> AgentResponse:
        responses: dict[str, str] = {}
        all_steps: list[AgentStep] = []
        total_tokens = TokenUsage()

        for role in self.agents.values():
            resp = await role.agent.run(query, **kwargs)
            responses[role.name] = resp.output
            all_steps.extend(resp.steps)
            total_tokens.input += resp.tokens_used.input
            total_tokens.output += resp.tokens_used.output
            total_tokens.total += resp.tokens_used.total

        # Synthesize: pick the first agent to summarize
        first_agent = next(iter(self.agents.values()))
        debate_summary = "\n".join(f"{name}: {answer}" for name, answer in responses.items())
        synthesis = await first_agent.agent.run(
            f"Synthesize these perspectives into a final answer:\n\n{debate_summary}",
            **kwargs,
        )
        total_tokens.input += synthesis.tokens_used.input
        total_tokens.output += synthesis.tokens_used.output
        total_tokens.total += synthesis.tokens_used.total

        return AgentResponse(output=synthesis.output, steps=all_steps, tokens_used=total_tokens)

    async def _run_hierarchical(self, query: str, **kwargs: Any) -> AgentResponse:
        # First agent is the manager, delegates to others
        agent_list = list(self.agents.values())
        if len(agent_list) < 2:
            return await self._run_sequential(query, **kwargs)

        manager = agent_list[0]
        workers = agent_list[1:]

        manager_resp = await manager.agent.run(
            f"You are a manager. Delegate this task to your team:\n{query}\n\n"
            f"Available workers: {', '.join(w.name for w in workers)}",
            **kwargs,
        )

        all_steps = list(manager_resp.steps)
        total_tokens = TokenUsage(
            input=manager_resp.tokens_used.input,
            output=manager_resp.tokens_used.output,
            total=manager_resp.tokens_used.total,
        )

        worker_results: list[str] = []
        for worker in workers:
            resp = await worker.agent.run(
                f"The manager assigned you this task: {manager_resp.output}\n"
                f"Original question: {query}",
                **kwargs,
            )
            worker_results.append(f"{worker.name}: {resp.output}")
            all_steps.extend(resp.steps)
            total_tokens.input += resp.tokens_used.input
            total_tokens.output += resp.tokens_used.output
            total_tokens.total += resp.tokens_used.total

        final = await manager.agent.run(
            f"Synthesize these worker results:\n" + "\n".join(worker_results) + f"\n\nOriginal: {query}",
            **kwargs,
        )
        total_tokens.input += final.tokens_used.input
        total_tokens.output += final.tokens_used.output
        total_tokens.total += final.tokens_used.total

        return AgentResponse(output=final.output, steps=all_steps, tokens_used=total_tokens)


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
