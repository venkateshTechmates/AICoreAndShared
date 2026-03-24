"""
Multi-Framework Orchestration — Adapters for LangChain, LangGraph, CrewAI, AutoGen, MCP.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class FrameworkAdapter(ABC):
    """Base class for framework adapters."""

    @abstractmethod
    def build_rag_chain(self, config: dict[str, Any]) -> Any:
        ...

    @staticmethod
    def for_framework(name: str, **kwargs: Any) -> FrameworkAdapter:
        adapters: dict[str, type[FrameworkAdapter]] = {
            "langchain": LangChainAdapter,
            "langgraph": LangGraphAdapter,
            "crewai": CrewAIAdapter,
            "autogen": AutoGenAdapter,
            "mcp": MCPAdapter,
        }
        cls = adapters.get(name.lower())
        if cls is None:
            raise ValueError(f"Unknown framework: {name}. Available: {list(adapters.keys())}")
        return cls(**kwargs)


class LangChainAdapter(FrameworkAdapter):
    """LangChain integration adapter."""

    def __init__(self, **kwargs: Any) -> None:
        self.kwargs = kwargs

    def build_rag_chain(self, config: dict[str, Any]) -> Any:
        """Build a LangChain RAG chain from ai_core config."""
        from langchain_core.output_parsers import StrOutputParser  # type: ignore[import-untyped]
        from langchain_core.prompts import ChatPromptTemplate  # type: ignore[import-untyped]
        from langchain_core.runnables import RunnablePassthrough  # type: ignore[import-untyped]
        from langchain_openai import ChatOpenAI, OpenAIEmbeddings  # type: ignore[import-untyped]

        llm = ChatOpenAI(
            model=config.get("llm_model", "gpt-4o"),
            temperature=config.get("temperature", 0.1),
        )
        prompt = ChatPromptTemplate.from_template(
            "Context:\n{context}\n\nQuestion: {question}\n\nAnswer:"
        )
        chain = (
            {"context": RunnablePassthrough(), "question": RunnablePassthrough()}
            | prompt
            | llm
            | StrOutputParser()
        )
        return chain

    def build_retriever(self, config: dict[str, Any]) -> Any:
        """Build a LangChain vector store retriever."""
        from langchain_community.vectorstores import Qdrant  # type: ignore[import-untyped]
        from langchain_openai import OpenAIEmbeddings  # type: ignore[import-untyped]

        embeddings = OpenAIEmbeddings(model=config.get("embedding_model", "text-embedding-3-large"))
        vectorstore = Qdrant.from_existing_collection(
            embedding=embeddings,
            collection_name=config.get("collection", "default"),
            url=config.get("url", "http://localhost:6333"),
        )
        return vectorstore.as_retriever(search_kwargs={"k": config.get("top_k", 10)})


class LangGraphAdapter(FrameworkAdapter):
    """LangGraph workflow adapter."""

    def __init__(self, **kwargs: Any) -> None:
        self.kwargs = kwargs

    def build_rag_chain(self, config: dict[str, Any]) -> Any:
        return self.build_workflow(config)

    def build_workflow(self, config: dict[str, Any]) -> Any:
        """Build a LangGraph stateful workflow."""
        from langgraph.graph import StateGraph, END  # type: ignore[import-untyped]
        from typing import TypedDict

        class State(TypedDict):
            question: str
            context: str
            answer: str

        def retrieve(state: State) -> State:
            state["context"] = f"[Retrieved context for: {state['question']}]"
            return state

        def generate(state: State) -> State:
            state["answer"] = f"[Generated answer from context]"
            return state

        graph = StateGraph(State)
        graph.add_node("retrieve", retrieve)
        graph.add_node("generate", generate)
        graph.set_entry_point("retrieve")
        graph.add_edge("retrieve", "generate")
        graph.add_edge("generate", END)

        return graph.compile()


class CrewAIAdapter(FrameworkAdapter):
    """CrewAI multi-agent adapter."""

    def __init__(self, **kwargs: Any) -> None:
        self.kwargs = kwargs

    def build_rag_chain(self, config: dict[str, Any]) -> Any:
        return self.build_crew(config)

    def build_crew(self, config: dict[str, Any]) -> Any:
        """Build a CrewAI crew for collaborative RAG."""
        from crewai import Agent, Crew, Task  # type: ignore[import-untyped]

        researcher = Agent(
            role="Researcher",
            goal="Find relevant information",
            backstory="Expert researcher with deep knowledge.",
            verbose=config.get("verbose", False),
        )
        analyst = Agent(
            role="Analyst",
            goal="Analyze and synthesize information",
            backstory="Expert analyst who provides clear insights.",
            verbose=config.get("verbose", False),
        )
        research_task = Task(
            description="Research: {query}",
            agent=researcher,
            expected_output="Relevant findings",
        )
        analysis_task = Task(
            description="Analyze the research findings and provide a comprehensive answer.",
            agent=analyst,
            expected_output="Final analysis",
        )
        crew = Crew(
            agents=[researcher, analyst],
            tasks=[research_task, analysis_task],
            verbose=config.get("verbose", False),
        )
        return crew


class AutoGenAdapter(FrameworkAdapter):
    """AutoGen group-chat adapter."""

    def __init__(self, **kwargs: Any) -> None:
        self.kwargs = kwargs

    def build_rag_chain(self, config: dict[str, Any]) -> Any:
        return self.build_group_chat(config)

    def build_group_chat(self, config: dict[str, Any]) -> Any:
        """Build an AutoGen group chat for collaborative problem-solving."""
        import autogen  # type: ignore[import-untyped]

        llm_config = {
            "model": config.get("llm_model", "gpt-4o"),
            "temperature": config.get("temperature", 0.1),
        }
        assistant = autogen.AssistantAgent(
            name="assistant",
            llm_config=llm_config,
        )
        user_proxy = autogen.UserProxyAgent(
            name="user",
            human_input_mode="NEVER",
            max_consecutive_auto_reply=config.get("max_rounds", 5),
        )
        return {"assistant": assistant, "user_proxy": user_proxy}


class MCPAdapter(FrameworkAdapter):
    """Model Context Protocol server adapter."""

    def __init__(self, **kwargs: Any) -> None:
        self.kwargs = kwargs
        self._tools: dict[str, Any] = {}
        self._resources: dict[str, Any] = {}

    def build_rag_chain(self, config: dict[str, Any]) -> Any:
        return self

    def tool(self, name: str | None = None):
        """Decorator to register an MCP tool."""

        def decorator(func: Any) -> Any:
            tool_name = name or func.__name__
            self._tools[tool_name] = func
            return func

        return decorator

    def resource(self, uri: str):
        """Decorator to register an MCP resource."""

        def decorator(func: Any) -> Any:
            self._resources[uri] = func
            return func

        return decorator

    def list_tools(self) -> list[dict[str, str]]:
        return [
            {"name": n, "description": getattr(f, "__doc__", "") or ""}
            for n, f in self._tools.items()
        ]

    def list_resources(self) -> list[str]:
        return list(self._resources.keys())
