"""
Tests for ai_shared.governance — PolicyEngine, AuditLogger, DataClassifier,
DataLineageTracker, RetentionManager, GDPRManager.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta

import pytest

from ai_shared.governance import (
    AuditLogger,
    DataClassifier,
    ClassificationLevel,
    DataLineageTracker,
    GDPRManager,
    Policy,
    PolicyEngine,
    RetentionManager,
    RetentionPolicy,
)


# ── PolicyEngine ──────────────────────────────────────────────────────────────


class TestPolicyEngine:
    def setup_method(self):
        self.engine = PolicyEngine()

    def test_no_policies_allows(self):
        result = self.engine.evaluate({"query": "hello"})
        assert result.allowed is True

    def test_deny_policy_blocks(self):
        self.engine.add_policy(Policy(
            name="block_ssn",
            condition="'ssn' in query",
            action="deny",
            description="Block SSN queries",
        ))
        result = self.engine.evaluate({"query": "show me ssn data"})
        assert result.allowed is False
        assert result.policy_name == "block_ssn"

    def test_allow_when_no_match(self):
        self.engine.add_policy(Policy(
            name="block_bad",
            condition="'bad' in query",
            action="deny",
        ))
        result = self.engine.evaluate({"query": "good query"})
        assert result.allowed is True

    def test_log_action_allowed_with_tag(self):
        self.engine.add_policy(Policy(
            name="log_sensitive",
            condition="'sensitive' in query",
            action="log",
            description="Log sensitive queries",
        ))
        result = self.engine.evaluate({"query": "sensitive data"})
        assert result.allowed is True
        assert result.action == "log"

    def test_disabled_policy_skipped(self):
        self.engine.add_policy(Policy(
            name="disabled",
            condition="True",
            action="deny",
            enabled=False,
        ))
        result = self.engine.evaluate({"query": "anything"})
        assert result.allowed is True

    def test_invalid_condition_skipped(self):
        self.engine.add_policy(Policy(
            name="bad_syntax",
            condition="this is not valid python $$%%",
            action="deny",
        ))
        result = self.engine.evaluate({"query": "test"})
        assert result.allowed is True


# ── AuditLogger ───────────────────────────────────────────────────────────────


class TestAuditLogger:
    def setup_method(self):
        self.logger = AuditLogger()

    def test_log_creates_entry(self):
        event_id = self.logger.log("admin", "create", "document_1")
        assert len(event_id) > 0
        entries = self.logger.query(actor="admin")
        assert len(entries) == 1

    def test_query_by_action(self):
        self.logger.log("user_a", "read", "file_1")
        self.logger.log("user_b", "write", "file_2")
        reads = self.logger.query(action="read")
        assert len(reads) == 1
        assert reads[0].actor == "user_a"

    def test_query_by_resource(self):
        self.logger.log("u1", "access", "resource_x")
        self.logger.log("u2", "access", "resource_y")
        results = self.logger.query(resource="resource_x")
        assert len(results) == 1

    def test_query_limit(self):
        for i in range(20):
            self.logger.log(f"user_{i}", "action", "resource")
        limited = self.logger.query(limit=5)
        assert len(limited) == 5

    def test_export_all(self):
        self.logger.log("a", "b", "c")
        exported = self.logger.export()
        assert len(exported) == 1
        assert "actor" in exported[0]

    def test_max_entries_enforced(self):
        small_logger = AuditLogger(max_entries=5)
        for i in range(10):
            small_logger.log(f"user_{i}", "action", "resource")
        assert len(small_logger._entries) == 5

    def test_outcome_recorded(self):
        self.logger.log("admin", "delete", "record_1", outcome="failure")
        entries = self.logger.query(actor="admin")
        assert entries[0].outcome == "failure"


# ── DataClassifier ────────────────────────────────────────────────────────────


class TestDataClassifier:
    def test_default_classification(self):
        classifier = DataClassifier()
        result = classifier.classify("normal text with no keywords")
        assert result.level == ClassificationLevel.INTERNAL

    def test_rule_based_classification(self):
        classifier = DataClassifier(rules={"ssn": ClassificationLevel.RESTRICTED})
        result = classifier.classify("This document contains ssn data")
        assert result.level == ClassificationLevel.RESTRICTED
        assert "ssn" in result.labels

    def test_multiple_rules(self):
        classifier = DataClassifier(rules={
            "patient": ClassificationLevel.RESTRICTED,
            "diagnosis": ClassificationLevel.CONFIDENTIAL,
        })
        result = classifier.classify("Patient diagnosis records")
        assert len(result.labels) == 2

    def test_add_rule(self):
        classifier = DataClassifier()
        classifier.add_rule("secret", ClassificationLevel.RESTRICTED)
        result = classifier.classify("This is a secret document")
        assert result.level == ClassificationLevel.RESTRICTED


# ── DataLineageTracker ────────────────────────────────────────────────────────


class TestDataLineageTracker:
    def setup_method(self):
        self.tracker = DataLineageTracker()

    def test_add_source(self):
        node_id = self.tracker.add_source("raw_data")
        assert node_id in self.tracker._nodes

    def test_add_transform(self):
        src = self.tracker.add_source("input")
        xfm = self.tracker.add_transform("clean", src, transform_desc="data cleaning")
        assert xfm in self.tracker._nodes
        assert len(self.tracker._edges) == 1

    def test_add_output(self):
        src = self.tracker.add_source("input")
        xfm = self.tracker.add_transform("process", src)
        out = self.tracker.add_output("result", xfm)
        assert out in self.tracker._nodes

    def test_get_lineage(self):
        src = self.tracker.add_source("raw")
        xfm = self.tracker.add_transform("transform", src)
        out = self.tracker.add_output("final", xfm)
        lineage = self.tracker.get_lineage(out)
        assert lineage["node"] is not None
        assert len(lineage["ancestors"]) == 2

    def test_to_dict(self):
        src = self.tracker.add_source("data")
        self.tracker.add_transform("process", src)
        data = self.tracker.to_dict()
        assert len(data["nodes"]) == 2
        assert len(data["edges"]) == 1


# ── RetentionManager ─────────────────────────────────────────────────────────


class TestRetentionManager:
    def setup_method(self):
        self.manager = RetentionManager()

    def test_add_and_get_policies(self):
        self.manager.add_policy(RetentionPolicy(
            name="test_policy", data_type="logs", retention_days=90,
        ))
        assert len(self.manager.get_policies()) == 1

    @pytest.mark.asyncio
    async def test_enforce_returns_actions(self):
        self.manager.add_policy(RetentionPolicy(
            name="logs", data_type="audit_logs", retention_days=30,
        ))
        actions = await self.manager.enforce()
        assert len(actions) == 1
        assert actions[0]["data_type"] == "audit_logs"

    @pytest.mark.asyncio
    async def test_disabled_policy_skipped(self):
        self.manager.add_policy(RetentionPolicy(
            name="disabled", data_type="temp", retention_days=1, enabled=False,
        ))
        actions = await self.manager.enforce()
        assert len(actions) == 0


# ── GDPRManager ───────────────────────────────────────────────────────────────


class TestGDPRManager:
    def setup_method(self):
        self.gdpr = GDPRManager()

    @pytest.mark.asyncio
    async def test_right_to_erasure(self):
        result = await self.gdpr.right_to_erasure(user_id="user_123")
        assert result["status"] == "completed"
        assert result["user_id"] == "user_123"

    @pytest.mark.asyncio
    async def test_erasure_logged(self):
        await self.gdpr.right_to_erasure(user_id="user_456")
        log = self.gdpr.get_erasure_log()
        assert len(log) == 1
        assert log[0]["user_id"] == "user_456"

    @pytest.mark.asyncio
    async def test_data_export(self):
        result = await self.gdpr.data_export(user_id="user_789")
        assert result["user_id"] == "user_789"
        assert "audit_trail" in result

    @pytest.mark.asyncio
    async def test_erasure_with_cascade(self):
        result = await self.gdpr.right_to_erasure(user_id="user_999", cascade=True)
        assert result["cascade"] is True

    @pytest.mark.asyncio
    async def test_erasure_without_cascade(self):
        result = await self.gdpr.right_to_erasure(user_id="user_000", cascade=False)
        assert result["cascade"] is False
        assert result["status"] == "completed"
