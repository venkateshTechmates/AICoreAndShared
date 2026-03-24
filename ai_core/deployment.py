"""
Multi-Region & Edge Deployment — PRD §19.

Provides: EdgeDeployment, GeoRouter, RegionConfig, HybridCloudManager.
Follows Strategy pattern for routing and Factory pattern for edge nodes.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable
from uuid import uuid4


# ── Enums & Config ───────────────────────────────────────────────────────────

class RoutingStrategy(str, Enum):
    GEO_LATENCY = "geo-latency"
    USER_LOCATION = "user-location"
    ROUND_ROBIN = "round-robin"
    WEIGHTED = "weighted"


class ReplicationStrategy(str, Enum):
    ACTIVE_ACTIVE = "active-active"
    ACTIVE_PASSIVE = "active-passive"


class Consistency(str, Enum):
    STRONG = "strong"
    EVENTUAL = "eventual"


@dataclass
class RegionConfig:
    name: str
    primary: bool = False
    vector_store_replica: bool = True
    llm_endpoint: str = ""
    data_residency: str = ""
    weight: float = 1.0
    healthy: bool = True
    latency_ms: float = 0.0


@dataclass
class EdgeConfig:
    locations: list[str] = field(default_factory=list)
    cache_strategy: str = "semantic"
    cache_ttl_seconds: int = 3600
    model_quantization: str = "fp16"
    max_batch_size: int = 10


@dataclass
class SyncConfig:
    enabled: bool = True
    strategy: ReplicationStrategy = ReplicationStrategy.ACTIVE_ACTIVE
    consistency: Consistency = Consistency.EVENTUAL
    sync_frequency_seconds: int = 30


@dataclass
class HybridConfig:
    cloud_provider: str = "aws"
    cloud_region: str = "us-east-1"
    cloud_vector_store: str = "pinecone"
    cloud_llm: str = "openai"
    on_prem_enabled: bool = False
    on_prem_vector_store: str = "qdrant"
    on_prem_models: list[str] = field(default_factory=list)
    fallback_strategy: str = "cloud-first"
    fallback_conditions: list[str] = field(default_factory=list)


# ── Geo Router ───────────────────────────────────────────────────────────────


class GeoRouter:
    """Route requests to the nearest / best-performing region."""

    def __init__(
        self,
        regions: list[RegionConfig],
        *,
        strategy: RoutingStrategy = RoutingStrategy.GEO_LATENCY,
        failover: bool = True,
    ) -> None:
        self._regions = regions
        self._strategy = strategy
        self._failover = failover
        self._round_robin_idx = 0

    async def route(self, *, user_location: str | None = None) -> RegionConfig:
        healthy = [r for r in self._regions if r.healthy]
        if not healthy:
            if not self._failover:
                raise RuntimeError("No healthy regions available")
            healthy = self._regions  # Try all regions as last resort

        if self._strategy == RoutingStrategy.GEO_LATENCY:
            return min(healthy, key=lambda r: r.latency_ms)
        elif self._strategy == RoutingStrategy.ROUND_ROBIN:
            region = healthy[self._round_robin_idx % len(healthy)]
            self._round_robin_idx += 1
            return region
        elif self._strategy == RoutingStrategy.WEIGHTED:
            import random

            weights = [r.weight for r in healthy]
            return random.choices(healthy, weights=weights, k=1)[0]
        else:
            # Default: return primary, fallback to first healthy
            primary = [r for r in healthy if r.primary]
            return primary[0] if primary else healthy[0]

    def mark_unhealthy(self, region_name: str) -> None:
        for r in self._regions:
            if r.name == region_name:
                r.healthy = False
                break

    def mark_healthy(self, region_name: str) -> None:
        for r in self._regions:
            if r.name == region_name:
                r.healthy = True
                break

    def update_latency(self, region_name: str, latency_ms: float) -> None:
        for r in self._regions:
            if r.name == region_name:
                r.latency_ms = latency_ms
                break


# ── Edge Deployment ──────────────────────────────────────────────────────────


@dataclass
class EdgeNode:
    id: str
    location: str
    status: str = "active"
    deployed_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    model_id: str = ""
    cache_hits: int = 0
    total_requests: int = 0


class EdgeDeployment:
    """Manage edge deployment locations for ultra-low latency inference."""

    def __init__(self, config: EdgeConfig) -> None:
        self.config = config
        self._nodes: dict[str, EdgeNode] = {}

    def deploy(self, location: str, *, model_id: str = "") -> EdgeNode:
        """Deploy or register an edge node at *location*."""
        node_id = uuid4().hex[:12]
        node = EdgeNode(id=node_id, location=location, model_id=model_id)
        self._nodes[node_id] = node
        return node

    def get_nearest(self, user_location: str) -> EdgeNode | None:
        """Return the nearest active edge node (simple location match)."""
        active = [n for n in self._nodes.values() if n.status == "active"]
        if not active:
            return None
        # Simple heuristic: prefer exact location match, else first active
        for node in active:
            if node.location == user_location:
                return node
        return active[0]

    def list_nodes(self) -> list[EdgeNode]:
        return list(self._nodes.values())

    def decommission(self, node_id: str) -> None:
        if node_id in self._nodes:
            self._nodes[node_id].status = "decommissioned"

    def get_stats(self) -> dict[str, Any]:
        return {
            "total_nodes": len(self._nodes),
            "active_nodes": sum(1 for n in self._nodes.values() if n.status == "active"),
            "total_requests": sum(n.total_requests for n in self._nodes.values()),
            "total_cache_hits": sum(n.cache_hits for n in self._nodes.values()),
        }


# ── Hybrid Cloud Manager ────────────────────────────────────────────────────


class HybridCloudManager:
    """Manage hybrid cloud + on-prem deployments with automatic fallback."""

    def __init__(self, config: HybridConfig) -> None:
        self.config = config
        self._on_prem_load: float = 0.0
        self._on_prem_latency_ms: float = 0.0

    def should_use_cloud(self) -> bool:
        """Determine whether to route to cloud based on fallback conditions."""
        if not self.config.on_prem_enabled:
            return True
        if self.config.fallback_strategy == "cloud-first":
            return True
        # Check conditions
        for condition in self.config.fallback_conditions:
            if "load" in condition and self._on_prem_load > 80:
                return True
            if "latency" in condition and self._on_prem_latency_ms > 1000:
                return True
        return False

    def update_on_prem_metrics(self, *, load: float = 0.0, latency_ms: float = 0.0) -> None:
        self._on_prem_load = load
        self._on_prem_latency_ms = latency_ms

    def get_llm_endpoint(self) -> str:
        if self.should_use_cloud():
            return self.config.cloud_llm
        return self.config.on_prem_models[0] if self.config.on_prem_models else self.config.cloud_llm

    def get_vector_store(self) -> str:
        if self.should_use_cloud():
            return self.config.cloud_vector_store
        return self.config.on_prem_vector_store


# ── Deployment Orchestrator ──────────────────────────────────────────────────


class DeploymentOrchestrator:
    """Coordinate multi-region, edge, and hybrid cloud deployments."""

    def __init__(
        self,
        regions: list[RegionConfig] | None = None,
        edge_config: EdgeConfig | None = None,
        hybrid_config: HybridConfig | None = None,
        *,
        routing_strategy: RoutingStrategy = RoutingStrategy.GEO_LATENCY,
    ) -> None:
        self._router = GeoRouter(
            regions or [],
            strategy=routing_strategy,
        )
        self._edge = EdgeDeployment(edge_config or EdgeConfig())
        self._hybrid = HybridCloudManager(hybrid_config or HybridConfig())
        self._health_checks: list[dict[str, Any]] = []

    @property
    def router(self) -> GeoRouter:
        return self._router

    @property
    def edge(self) -> EdgeDeployment:
        return self._edge

    @property
    def hybrid(self) -> HybridCloudManager:
        return self._hybrid

    async def health_check(self) -> dict[str, Any]:
        """Run a comprehensive health check across all deployment layers."""
        result: dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "edge": self._edge.get_stats(),
            "hybrid_cloud_target": "cloud" if self._hybrid.should_use_cloud() else "on-prem",
        }
        self._health_checks.append(result)
        return result
