"""
Tests for ai_core.agents — Multi-agent orchestration, coordination modes,
message bus, pipeline builder, and agent state management.
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai_core.agents import (
    AgentExecutor,
    AgentPipelineBuilder,
    AgentRole,
    AgentState,
    BaseAgent,
    CoordinationMode,
    ConflictResolution,
    MessageBus,
    AgentMessage,
    MultiAgentSystem,
    ReActAgent,
    PlanExecuteAgent,
    ReflexionAgent,
    FunctionCallAgent,
    StructuredOutputAgent,
    Tool,
    ToolRegistry,
    tool,
)
from ai_core.schemas import AgentResponse, AgentStep, AgentType, TokenUsage


# ── Fixtures ──────────────────────────────────────────────────────────────────


class MockLLM:
    """Test-friendly mock LLM that returns predictable responses."""

    def __init__(self, response_text: str = "Mock answer", *, final: bool = True) -> None:
        self._text = response_text
        self._final = final

    async def generate(self, prompt: str) -> MagicMock:
        resp = MagicMock()
        text = self._text
        if self._final:
            text = f"Final Answer: {self._text}"
        resp.text = text
        resp.usage = MagicMock(input=10, output=5, total=15)
        return resp

    async def chat(self, messages: list) -> MagicMock:
        resp = MagicMock()
        text = self._text
        if self._final:
            text = f"Final Answer: {self._text}"
        resp.text = text
        resp.usage = MagicMock(input=10, output=5, total=15)
        return resp


class MockAgent(BaseAgent):
    """Simple mock agent that returns a fixed response."""

    def __init__(self, output: str = "mock output", **kwargs):
        super().__init__(llm=MockLLM(), **kwargs)
        self._output = output

    async def run(self, query: str, **kwargs) -> AgentResponse:
        return AgentResponse(
            output=self._output,
            steps=[AgentStep(thought=f"Processing: {query[:50]}")],
            tokens_used=TokenUsage(input=10, output=5, total=15),
        )


@pytest.fixture
def mock_llm():
    return MockLLM()


@pytest.fixture
def mock_agent():
    return MockAgent()


@pytest.fixture
def bus():
    return MessageBus()


# ── Tool Registry ─────────────────────────────────────────────────────────────


class TestToolRegistry:
    def setup_method(self):
        ToolRegistry.clear()

    def test_register_tool_instance(self):
        t = Tool()
        t.name = "test_tool"
        t.description = "A test tool"
        ToolRegistry.register(t)
        assert ToolRegistry.get("test_tool").name == "test_tool"

    def test_register_tool_class(self):
        class MyTool(Tool):
            name = "my_tool"
            description = "My tool"
        ToolRegistry.register(MyTool)
        assert ToolRegistry.get("my_tool").name == "my_tool"

    def test_get_unknown_tool_raises(self):
        with pytest.raises(KeyError, match="Tool not found"):
            ToolRegistry.get("nonexistent")

    def test_list_tools(self):
        t = Tool()
        t.name = "listed"
        t.description = "Listed tool"
        ToolRegistry.register(t)
        tools = ToolRegistry.list_tools()
        assert len(tools) == 1
        assert tools[0].name == "listed"

    def test_clear(self):
        t = Tool()
        t.name = "temp"
        ToolRegistry.register(t)
        ToolRegistry.clear()
        assert len(ToolRegistry.list_tools()) == 0

    def test_tool_decorator(self):
        ToolRegistry.clear()

        @tool("decorated", "A decorated tool")
        async def my_func(x: str) -> str:
            return x

        assert "decorated" in ToolRegistry._tools


# ── Message Bus ───────────────────────────────────────────────────────────────


class TestMessageBus:
    def test_publish_and_history(self, bus):
        msg = AgentMessage(sender="agent_a", content="hello")
        bus.publish(msg)
        history = bus.get_history()
        assert len(history) == 1
        assert history[0].sender == "agent_a"

    def test_subscribe_receives_messages(self, bus):
        received = []
        bus.subscribe("agent_b", lambda m: received.append(m))
        bus.publish(AgentMessage(sender="agent_a", recipient="agent_b", content="hi"))
        assert len(received) == 1

    def test_broadcast_to_all_subscribers(self, bus):
        received_a, received_b = [], []
        bus.subscribe("__broadcast__", lambda m: received_a.append(m))
        bus.subscribe("__broadcast__", lambda m: received_b.append(m))
        bus.publish(AgentMessage(sender="system", content="broadcast"))
        assert len(received_a) == 1
        assert len(received_b) == 1

    def test_dead_letter_on_handler_error(self, bus):
        def bad_handler(msg):
            raise RuntimeError("Handler crashed")
        bus.subscribe("agent_x", bad_handler)
        bus.publish(AgentMessage(sender="system", recipient="agent_x", content="boom"))
        assert len(bus.get_dead_letters()) == 1

    def test_filter_by_sender(self, bus):
        bus.publish(AgentMessage(sender="a", content="1"))
        bus.publish(AgentMessage(sender="b", content="2"))
        assert len(bus.get_history(sender="a")) == 1

    def test_filter_by_recipient(self, bus):
        bus.publish(AgentMessage(sender="a", recipient="x", content="1"))
        bus.publish(AgentMessage(sender="b", recipient="y", content="2"))
        assert len(bus.get_history(recipient="x")) == 1

    def test_clear(self, bus):
        bus.publish(AgentMessage(sender="a", content="1"))
        bus.clear()
        assert len(bus.get_history()) == 0


# ── Agent Factory ─────────────────────────────────────────────────────────────


class TestAgentExecutor:
    def test_create_react(self, mock_llm):
        agent = AgentExecutor.create(AgentType.REACT, mock_llm)
        assert isinstance(agent, ReActAgent)

    def test_create_plan_execute(self, mock_llm):
        agent = AgentExecutor.create(AgentType.PLAN_EXECUTE, mock_llm)
        assert isinstance(agent, PlanExecuteAgent)

    def test_create_reflexion(self, mock_llm):
        agent = AgentExecutor.create(AgentType.REFLEXION, mock_llm)
        assert isinstance(agent, ReflexionAgent)

    def test_create_function_call(self, mock_llm):
        agent = AgentExecutor.create(AgentType.FUNCTION_CALL, mock_llm)
        assert isinstance(agent, FunctionCallAgent)

    def test_create_structured(self, mock_llm):
        agent = AgentExecutor.create(AgentType.STRUCTURED, mock_llm)
        assert isinstance(agent, StructuredOutputAgent)

    def test_create_from_string(self, mock_llm):
        agent = AgentExecutor.create("react", mock_llm)
        assert isinstance(agent, ReActAgent)

    def test_create_unknown_raises(self, mock_llm):
        with pytest.raises(ValueError):
            AgentExecutor.create("nonexistent", mock_llm)


# ── ReAct Agent ───────────────────────────────────────────────────────────────


class TestReActAgent:
    @pytest.mark.asyncio
    async def test_returns_final_answer(self):
        llm = MockLLM("The answer is 42")
        agent = ReActAgent(llm)
        result = await agent.run("What is the answer?")
        assert "42" in result.output
        assert result.tokens_used.total > 0

    @pytest.mark.asyncio
    async def test_max_iterations_respected(self):
        llm = MockLLM("thinking...", final=False)
        agent = ReActAgent(llm, max_iterations=2)
        result = await agent.run("loop test")
        assert "Max iterations" in result.output


# ── Multi-Agent System: Sequential ────────────────────────────────────────────


class TestSequentialCoordination:
    @pytest.mark.asyncio
    async def test_sequential_runs_all_agents(self):
        agents = [
            AgentRole("agent_a", MockAgent("answer from A")),
            AgentRole("agent_b", MockAgent("answer from B")),
        ]
        system = MultiAgentSystem(agents, coordination="sequential")
        result = await system.run("test query")
        assert result.output == "answer from B"
        assert "agent_a" in result.agent_outputs
        assert "agent_b" in result.agent_outputs

    @pytest.mark.asyncio
    async def test_sequential_passes_context(self):
        agents = [
            AgentRole("first", MockAgent("step 1 done")),
            AgentRole("second", MockAgent("step 2 done")),
            AgentRole("third", MockAgent("step 3 done")),
        ]
        system = MultiAgentSystem(agents, coordination="sequential")
        result = await system.run("chain query")
        assert len(result.agent_outputs) == 3
        assert result.tokens_used.total > 0

    @pytest.mark.asyncio
    async def test_sequential_publishes_messages(self):
        bus = MessageBus()
        agents = [
            AgentRole("a", MockAgent("out_a")),
            AgentRole("b", MockAgent("out_b")),
        ]
        system = MultiAgentSystem(agents, coordination="sequential", message_bus=bus)
        await system.run("test")
        assert len(bus.get_history()) == 2


# ── Multi-Agent System: Parallel ──────────────────────────────────────────────


class TestParallelCoordination:
    @pytest.mark.asyncio
    async def test_parallel_runs_all(self):
        agents = [
            AgentRole("fast", MockAgent("fast result")),
            AgentRole("slow", MockAgent("slow result")),
        ]
        system = MultiAgentSystem(agents, coordination="parallel")
        result = await system.run("parallel query")
        assert "fast" in result.agent_outputs
        assert "slow" in result.agent_outputs

    @pytest.mark.asyncio
    async def test_parallel_merged_output(self):
        agents = [
            AgentRole("a", MockAgent("res_a")),
            AgentRole("b", MockAgent("res_b")),
        ]
        system = MultiAgentSystem(agents, coordination="parallel")
        result = await system.run("merged")
        assert "[a]" in result.output
        assert "[b]" in result.output


# ── Multi-Agent System: Debate ────────────────────────────────────────────────


class TestDebateCoordination:
    @pytest.mark.asyncio
    async def test_debate_produces_conflict_resolution(self):
        agents = [
            AgentRole("expert_a", MockAgent("perspective A")),
            AgentRole("expert_b", MockAgent("perspective B")),
        ]
        system = MultiAgentSystem(agents, coordination="debate", max_rounds=2)
        result = await system.run("debate topic")
        assert result.conflict_resolution is not None
        assert result.conflict_resolution.strategy == "debate_consensus"

    @pytest.mark.asyncio
    async def test_debate_all_agents_contribute(self):
        agents = [
            AgentRole("a", MockAgent("view_a")),
            AgentRole("b", MockAgent("view_b")),
            AgentRole("c", MockAgent("view_c")),
        ]
        system = MultiAgentSystem(agents, coordination="debate", max_rounds=1)
        result = await system.run("multi-view debate")
        assert len(result.agent_outputs) == 3


# ── Multi-Agent System: Hierarchical ─────────────────────────────────────────


class TestHierarchicalCoordination:
    @pytest.mark.asyncio
    async def test_hierarchical_manager_worker(self):
        agents = [
            AgentRole("manager", MockAgent("delegate tasks"), role_description="Team manager"),
            AgentRole("worker_1", MockAgent("task 1 done"), role_description="Researcher"),
            AgentRole("worker_2", MockAgent("task 2 done"), role_description="Analyst"),
        ]
        system = MultiAgentSystem(agents, coordination="hierarchical")
        result = await system.run("complex task")
        assert "manager" in result.agent_outputs
        assert "worker_1" in result.agent_outputs
        assert "worker_2" in result.agent_outputs

    @pytest.mark.asyncio
    async def test_hierarchical_single_agent_fallback(self):
        agents = [AgentRole("solo", MockAgent("solo answer"))]
        system = MultiAgentSystem(agents, coordination="hierarchical")
        result = await system.run("solo query")
        assert result.output == "solo answer"


# ── Multi-Agent System: Swarm ─────────────────────────────────────────────────


class TestSwarmCoordination:
    @pytest.mark.asyncio
    async def test_swarm_routes_by_domain(self):
        agents = [
            AgentRole("medical", MockAgent("medical answer"), domain="medical", priority=5),
            AgentRole("legal", MockAgent("legal answer"), domain="legal", priority=5),
        ]
        system = MultiAgentSystem(agents, coordination="swarm")
        result = await system.run("medical question about diagnosis")
        assert "medical" in result.agent_outputs

    @pytest.mark.asyncio
    async def test_swarm_fallback_all_agents(self):
        agents = [
            AgentRole("a", MockAgent("answer_a"), domain="specific"),
            AgentRole("b", MockAgent("answer_b"), domain="niche"),
        ]
        system = MultiAgentSystem(agents, coordination="swarm")
        result = await system.run("general query no matching domain")
        assert len(result.agent_outputs) >= 1

    @pytest.mark.asyncio
    async def test_swarm_priority_routing(self):
        agents = [
            AgentRole("low", MockAgent("low_pri"), domain="test", priority=1),
            AgentRole("high", MockAgent("high_pri"), domain="test", priority=10),
        ]
        system = MultiAgentSystem(agents, coordination="swarm")
        result = await system.run("test query")
        # High priority agent should be tried first and its output returned
        assert result.output == "high_pri"


# ── Multi-Agent System: Supervisor ────────────────────────────────────────────


class TestSupervisorCoordination:
    @pytest.mark.asyncio
    async def test_supervisor_routes_to_workers(self):
        agents = [
            AgentRole("supervisor", MockAgent("CALL worker_a"), role_description="Supervisor"),
            AgentRole("worker_a", MockAgent("worker_a result"), role_description="Worker A"),
        ]
        system = MultiAgentSystem(agents, coordination="supervisor", max_rounds=2)
        result = await system.run("supervised task")
        assert len(result.agent_outputs) >= 1

    @pytest.mark.asyncio
    async def test_supervisor_done_terminates(self):
        agents = [
            AgentRole("supervisor", MockAgent("DONE final answer"), role_description="Supervisor"),
            AgentRole("worker", MockAgent("worker result"), role_description="Worker"),
        ]
        system = MultiAgentSystem(agents, coordination="supervisor", max_rounds=3)
        result = await system.run("finish test")
        assert "final answer" in result.output


# ── Policy Guard ──────────────────────────────────────────────────────────────


class TestPolicyGuard:
    @pytest.mark.asyncio
    async def test_policy_blocks_query(self):
        agents = [AgentRole("a", MockAgent("should not run"))]
        system = MultiAgentSystem(
            agents, coordination="sequential",
            policy_check=lambda q, _: False,
        )
        result = await system.run("blocked query")
        assert "blocked" in result.output.lower()

    @pytest.mark.asyncio
    async def test_policy_allows_query(self):
        agents = [AgentRole("a", MockAgent("allowed result"))]
        system = MultiAgentSystem(
            agents, coordination="sequential",
            policy_check=lambda q, _: True,
        )
        result = await system.run("safe query")
        assert result.output == "allowed result"


# ── Pipeline Builder ──────────────────────────────────────────────────────────


class TestAgentPipelineBuilder:
    def test_builds_sequential_pipeline(self):
        builder = AgentPipelineBuilder()
        system = (
            builder
            .add_agent("a", MockAgent("out_a"))
            .add_agent("b", MockAgent("out_b"))
            .with_coordination("sequential")
            .build()
        )
        assert isinstance(system, MultiAgentSystem)
        assert system.coordination == CoordinationMode.SEQUENTIAL
        assert len(system.agents) == 2

    def test_builds_with_all_options(self):
        bus = MessageBus()
        system = (
            AgentPipelineBuilder()
            .add_agent("x", MockAgent(), role_description="Test", priority=5, domain="test")
            .with_coordination(CoordinationMode.DEBATE)
            .with_max_rounds(5)
            .with_cost_limit(100.0)
            .with_policy_check(lambda q, _: True)
            .with_message_bus(bus)
            .build()
        )
        assert system.coordination == CoordinationMode.DEBATE
        assert system.max_rounds == 5
        assert system.cost_limit_usd == 100.0
        assert system.bus is bus


# ── Orchestration Result ──────────────────────────────────────────────────────


class TestOrchestrationResult:
    @pytest.mark.asyncio
    async def test_result_has_elapsed_time(self):
        agents = [AgentRole("a", MockAgent("done"))]
        system = MultiAgentSystem(agents, coordination="sequential")
        result = await system.run("timing test")
        assert result.elapsed_seconds >= 0

    @pytest.mark.asyncio
    async def test_result_tracks_messages(self):
        bus = MessageBus()
        agents = [AgentRole("a", MockAgent("out")), AgentRole("b", MockAgent("out"))]
        system = MultiAgentSystem(agents, coordination="sequential", message_bus=bus)
        result = await system.run("msg test")
        assert result.messages_exchanged == 2

    @pytest.mark.asyncio
    async def test_run_log_recorded(self):
        agents = [AgentRole("a", MockAgent("out"))]
        system = MultiAgentSystem(agents, coordination="sequential")
        await system.run("log test 1")
        await system.run("log test 2")
        assert len(system.get_run_log()) == 2

    @pytest.mark.asyncio
    async def test_agent_states_tracked(self):
        agents = [AgentRole("a", MockAgent("out"))]
        system = MultiAgentSystem(agents, coordination="sequential")
        await system.run("state test")
        states = system.get_agent_states()
        assert states["a"] == "completed"
