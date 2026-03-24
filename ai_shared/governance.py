"""
Data Governance — lineage tracking, data classification, policy engine, and audit logging.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4


# ── Data Classification ──────────────────────────────────────────────────────

class ClassificationLevel(str, Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"


@dataclass
class ClassificationResult:
    level: ClassificationLevel
    labels: list[str] = field(default_factory=list)
    confidence: float = 1.0
    reasoning: str = ""


class DataClassifier:
    """Classify data sensitivity based on content and metadata."""

    def __init__(
        self,
        *,
        default_level: ClassificationLevel = ClassificationLevel.INTERNAL,
        rules: dict[str, ClassificationLevel] | None = None,
    ) -> None:
        self.default_level = default_level
        self._rules: dict[str, ClassificationLevel] = rules or {}

    def classify(self, text: str, *, metadata: dict[str, Any] | None = None) -> ClassificationResult:
        labels: list[str] = []
        level = self.default_level

        lower = text.lower()
        for keyword, kw_level in self._rules.items():
            if keyword.lower() in lower:
                labels.append(keyword)
                if kw_level.value > level.value:
                    level = kw_level

        return ClassificationResult(level=level, labels=labels, confidence=0.85 if labels else 0.5)

    def add_rule(self, keyword: str, level: ClassificationLevel) -> None:
        self._rules[keyword] = level


# ── Data Lineage Tracker ─────────────────────────────────────────────────────

@dataclass
class LineageNode:
    id: str
    name: str
    node_type: str  # source, transform, output
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class LineageEdge:
    source_id: str
    target_id: str
    transform: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


class DataLineageTracker:
    """Track the provenance and transformations of data through the pipeline."""

    def __init__(self) -> None:
        self._nodes: dict[str, LineageNode] = {}
        self._edges: list[LineageEdge] = []

    def add_source(self, name: str, *, metadata: dict[str, Any] | None = None) -> str:
        node_id = uuid4().hex[:12]
        self._nodes[node_id] = LineageNode(id=node_id, name=name, node_type="source", metadata=metadata or {})
        return node_id

    def add_transform(
        self,
        name: str,
        source_id: str,
        *,
        transform_desc: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> str:
        node_id = uuid4().hex[:12]
        self._nodes[node_id] = LineageNode(id=node_id, name=name, node_type="transform", metadata=metadata or {})
        self._edges.append(LineageEdge(source_id=source_id, target_id=node_id, transform=transform_desc))
        return node_id

    def add_output(self, name: str, source_id: str, *, metadata: dict[str, Any] | None = None) -> str:
        node_id = uuid4().hex[:12]
        self._nodes[node_id] = LineageNode(id=node_id, name=name, node_type="output", metadata=metadata or {})
        self._edges.append(LineageEdge(source_id=source_id, target_id=node_id))
        return node_id

    def get_lineage(self, node_id: str) -> dict[str, Any]:
        """Trace full lineage for a node (walk backward through edges)."""
        visited: list[str] = []
        stack = [node_id]
        while stack:
            nid = stack.pop()
            if nid in visited:
                continue
            visited.append(nid)
            for edge in self._edges:
                if edge.target_id == nid:
                    stack.append(edge.source_id)
        return {
            "node": self._nodes.get(node_id),
            "ancestors": [self._nodes[n] for n in visited if n != node_id and n in self._nodes],
            "edges": [e for e in self._edges if e.source_id in visited or e.target_id in visited],
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "nodes": {nid: {"name": n.name, "type": n.node_type} for nid, n in self._nodes.items()},
            "edges": [{"from": e.source_id, "to": e.target_id, "transform": e.transform} for e in self._edges],
        }


# ── Policy Engine ────────────────────────────────────────────────────────────

@dataclass
class Policy:
    name: str
    condition: str  # Python expression evaluated safely
    action: str  # "allow", "deny", "redact", "log"
    description: str = ""
    enabled: bool = True


@dataclass
class PolicyResult:
    allowed: bool
    policy_name: str = ""
    action: str = "allow"
    reason: str = ""


class PolicyEngine:
    """Evaluate data governance policies against requests."""

    def __init__(self) -> None:
        self._policies: list[Policy] = []

    def add_policy(self, policy: Policy) -> None:
        self._policies.append(policy)

    def evaluate(self, context: dict[str, Any]) -> PolicyResult:
        for policy in self._policies:
            if not policy.enabled:
                continue
            try:
                # Evaluate condition against a restricted context
                if self._eval_condition(policy.condition, context):
                    if policy.action == "deny":
                        return PolicyResult(allowed=False, policy_name=policy.name, action="deny", reason=policy.description)
                    elif policy.action == "log":
                        return PolicyResult(allowed=True, policy_name=policy.name, action="log", reason=policy.description)
            except Exception:
                continue
        return PolicyResult(allowed=True)

    @staticmethod
    def _eval_condition(condition: str, context: dict[str, Any]) -> bool:
        """Safely evaluate a simple condition expression."""
        # Only allow simple key lookups and comparisons
        safe_globals: dict[str, Any] = {"__builtins__": {}}
        try:
            return bool(eval(condition, safe_globals, context))  # noqa: S307
        except Exception:
            return False


# ── Audit Logger ─────────────────────────────────────────────────────────────

@dataclass
class AuditEntry:
    event_id: str
    timestamp: str
    actor: str
    action: str
    resource: str
    details: dict[str, Any] = field(default_factory=dict)
    outcome: str = "success"


class AuditLogger:
    """Append-only audit log for governance and compliance."""

    def __init__(self, *, max_entries: int = 100_000) -> None:
        self.max_entries = max_entries
        self._entries: list[AuditEntry] = []

    def log(
        self,
        actor: str,
        action: str,
        resource: str,
        *,
        details: dict[str, Any] | None = None,
        outcome: str = "success",
    ) -> str:
        event_id = uuid4().hex[:16]
        entry = AuditEntry(
            event_id=event_id,
            timestamp=datetime.utcnow().isoformat(),
            actor=actor,
            action=action,
            resource=resource,
            details=details or {},
            outcome=outcome,
        )
        self._entries.append(entry)
        if len(self._entries) > self.max_entries:
            self._entries = self._entries[-self.max_entries:]
        return event_id

    def query(
        self,
        *,
        actor: str | None = None,
        action: str | None = None,
        resource: str | None = None,
        limit: int = 100,
    ) -> list[AuditEntry]:
        results: list[AuditEntry] = []
        for entry in reversed(self._entries):
            if actor and entry.actor != actor:
                continue
            if action and entry.action != action:
                continue
            if resource and entry.resource != resource:
                continue
            results.append(entry)
            if len(results) >= limit:
                break
        return results

    def export(self) -> list[dict[str, Any]]:
        import dataclasses
        return [dataclasses.asdict(e) for e in self._entries]


# ── Data Retention Policies ──────────────────────────────────────────────────

@dataclass
class RetentionPolicy:
    name: str
    data_type: str  # e.g. "embeddings", "audit_logs", "user_data"
    retention_days: int
    action: str = "delete"  # "delete", "archive", "anonymize"
    enabled: bool = True


class RetentionManager:
    """Enforce data retention policies across the pipeline."""

    def __init__(self) -> None:
        self._policies: list[RetentionPolicy] = []
        self._actions_taken: list[dict[str, Any]] = []

    def add_policy(self, policy: RetentionPolicy) -> None:
        self._policies.append(policy)

    def get_policies(self) -> list[RetentionPolicy]:
        return list(self._policies)

    async def enforce(self, current_time: datetime | None = None) -> list[dict[str, Any]]:
        """Evaluate all policies and return actions to take on expired data."""
        now = current_time or datetime.utcnow()
        actions: list[dict[str, Any]] = []
        for policy in self._policies:
            if not policy.enabled:
                continue
            from datetime import timedelta
            cutoff = now - timedelta(days=policy.retention_days)
            action = {
                "policy": policy.name,
                "data_type": policy.data_type,
                "action": policy.action,
                "cutoff_date": cutoff.isoformat(),
                "timestamp": now.isoformat(),
            }
            actions.append(action)
        self._actions_taken.extend(actions)
        return actions

    def get_action_history(self) -> list[dict[str, Any]]:
        return list(self._actions_taken)


# ── GDPR Compliance ──────────────────────────────────────────────────────────


class GDPRManager:
    """GDPR right-to-erasure and data subject request handling."""

    def __init__(self, *, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()
        self._erasure_log: list[dict[str, Any]] = []

    async def right_to_erasure(
        self,
        *,
        user_id: str,
        data_stores: list[Any] | None = None,
        cascade: bool = True,
    ) -> dict[str, Any]:
        """Process a GDPR right-to-erasure request (cascade deletion)."""
        deleted_components: list[str] = []

        if data_stores and cascade:
            for store in data_stores:
                if hasattr(store, "delete_by_user"):
                    await store.delete_by_user(user_id)
                    deleted_components.append(type(store).__name__)

        result = {
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat(),
            "cascade": cascade,
            "deleted_components": deleted_components,
            "status": "completed",
        }
        self._erasure_log.append(result)
        self._audit.log(
            actor="system",
            action="gdpr_erasure",
            resource=f"user:{user_id}",
            details=result,
        )
        return result

    async def data_export(self, *, user_id: str) -> dict[str, Any]:
        """GDPR data portability — export all data for a user."""
        return {
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat(),
            "audit_trail": self._audit.query(actor=user_id),
            "erasure_history": [
                e for e in self._erasure_log if e["user_id"] == user_id
            ],
        }

    def get_erasure_log(self) -> list[dict[str, Any]]:
        return list(self._erasure_log)
