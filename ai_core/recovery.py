"""
Disaster Recovery & High Availability — PRD §20.

Provides: BackupManager, RestorePoint, DRTest, ChaosEngineering,
          FailoverChain, HAConfig.
Follows SRP (each class handles one concern) and OCP (extensible backends).
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, AsyncIterator, Callable
from uuid import uuid4


# ── Configuration ────────────────────────────────────────────────────────────

@dataclass
class HAConfig:
    """High-availability configuration for vector stores and LLM endpoints."""

    replication_factor: int = 3
    read_replicas: int = 2
    auto_failover: bool = True
    recovery_point_objective_seconds: int = 60
    recovery_time_objective_minutes: int = 15


@dataclass
class RestorePoint:
    """Represents a point-in-time recovery target."""

    timestamp: str
    includes: list[str] = field(default_factory=lambda: ["vector_store", "metadata"])
    backup_id: str = ""
    verified: bool = False


@dataclass
class BackupRecord:
    """Metadata for a completed backup."""

    id: str
    timestamp: str
    backend: str
    destination: str
    size_bytes: int = 0
    encrypted: bool = False
    compressed: bool = False
    verified: bool = False
    components: list[str] = field(default_factory=list)


# ── Failover Chain ───────────────────────────────────────────────────────────


class FailoverChain:
    """LLM endpoint failover with circuit-breaker integration."""

    def __init__(
        self,
        providers: list[str],
        *,
        failure_threshold: int = 5,
        recovery_timeout_seconds: int = 60,
    ) -> None:
        self._providers = providers
        self._failure_threshold = failure_threshold
        self._recovery_timeout = recovery_timeout_seconds
        self._failure_counts: dict[str, int] = {p: 0 for p in providers}
        self._circuit_open_at: dict[str, float] = {}

    def get_active_provider(self) -> str:
        """Return the first provider whose circuit is not open."""
        now = time.time()
        for provider in self._providers:
            open_at = self._circuit_open_at.get(provider)
            if open_at is not None:
                if now - open_at < self._recovery_timeout:
                    continue  # Circuit still open
                else:
                    # Recovery timeout elapsed, try again (half-open)
                    del self._circuit_open_at[provider]
                    self._failure_counts[provider] = 0

            if self._failure_counts.get(provider, 0) < self._failure_threshold:
                return provider
        # All circuits open — return first as last resort
        return self._providers[0]

    def record_success(self, provider: str) -> None:
        self._failure_counts[provider] = 0
        self._circuit_open_at.pop(provider, None)

    def record_failure(self, provider: str) -> None:
        self._failure_counts[provider] = self._failure_counts.get(provider, 0) + 1
        if self._failure_counts[provider] >= self._failure_threshold:
            self._circuit_open_at[provider] = time.time()

    def status(self) -> dict[str, Any]:
        now = time.time()
        return {
            provider: {
                "failures": self._failure_counts.get(provider, 0),
                "circuit_open": provider in self._circuit_open_at
                and (now - self._circuit_open_at[provider]) < self._recovery_timeout,
            }
            for provider in self._providers
        }


# ── Backup Manager ───────────────────────────────────────────────────────────


class BaseBackupBackend(ABC):
    """Abstract backend for backup storage (S3, GCS, Azure Blob, local)."""

    @abstractmethod
    async def store(self, data: bytes, destination: str) -> str:
        ...

    @abstractmethod
    async def retrieve(self, backup_id: str) -> bytes:
        ...

    @abstractmethod
    async def list_backups(self, prefix: str = "") -> list[str]:
        ...


class S3BackupBackend(BaseBackupBackend):
    """AWS S3 backup backend."""

    def __init__(self, *, bucket: str = "ai-backups", region: str = "us-east-1") -> None:
        self._bucket = bucket
        self._region = region

    async def store(self, data: bytes, destination: str) -> str:
        import asyncio

        def _upload() -> str:
            import boto3  # type: ignore[import-untyped]

            s3 = boto3.client("s3", region_name=self._region)
            s3.put_object(Bucket=self._bucket, Key=destination, Body=data)
            return f"s3://{self._bucket}/{destination}"

        return await asyncio.get_event_loop().run_in_executor(None, _upload)

    async def retrieve(self, backup_id: str) -> bytes:
        import asyncio

        def _download() -> bytes:
            import boto3  # type: ignore[import-untyped]

            s3 = boto3.client("s3", region_name=self._region)
            obj = s3.get_object(Bucket=self._bucket, Key=backup_id)
            return obj["Body"].read()

        return await asyncio.get_event_loop().run_in_executor(None, _download)

    async def list_backups(self, prefix: str = "") -> list[str]:
        import asyncio

        def _list() -> list[str]:
            import boto3  # type: ignore[import-untyped]

            s3 = boto3.client("s3", region_name=self._region)
            resp = s3.list_objects_v2(Bucket=self._bucket, Prefix=prefix)
            return [obj["Key"] for obj in resp.get("Contents", [])]

        return await asyncio.get_event_loop().run_in_executor(None, _list)


class LocalBackupBackend(BaseBackupBackend):
    """Local filesystem backup backend (for dev/testing)."""

    def __init__(self, *, base_path: str = "/tmp/ai-backups") -> None:
        self._base_path = base_path

    async def store(self, data: bytes, destination: str) -> str:
        import os

        full_path = os.path.join(self._base_path, destination)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "wb") as f:
            f.write(data)
        return full_path

    async def retrieve(self, backup_id: str) -> bytes:
        import os

        full_path = os.path.join(self._base_path, backup_id)
        with open(full_path, "rb") as f:
            return f.read()

    async def list_backups(self, prefix: str = "") -> list[str]:
        import os

        target = os.path.join(self._base_path, prefix)
        if not os.path.exists(target):
            return []
        results: list[str] = []
        for root, _dirs, files in os.walk(target):
            for fname in files:
                results.append(os.path.relpath(os.path.join(root, fname), self._base_path))
        return results


_BACKEND_REGISTRY: dict[str, type[BaseBackupBackend]] = {
    "s3": S3BackupBackend,
    "local": LocalBackupBackend,
}


class BackupManager:
    """Manage backup and restore operations for AI pipeline data."""

    def __init__(
        self,
        *,
        backend: str = "local",
        encryption: bool = False,
        compression: bool = True,
        backend_config: dict[str, Any] | None = None,
    ) -> None:
        cls = _BACKEND_REGISTRY.get(backend)
        if cls is None:
            raise ValueError(f"Unsupported backup backend: {backend}")
        self._backend = cls(**(backend_config or {}))
        self._encryption = encryption
        self._compression = compression
        self._records: list[BackupRecord] = []

    async def backup(
        self,
        data: bytes,
        *,
        destination: str,
        components: list[str] | None = None,
    ) -> BackupRecord:
        """Perform a backup of the provided data."""
        if self._compression:
            import zlib

            data = zlib.compress(data)

        location = await self._backend.store(data, destination)
        record = BackupRecord(
            id=uuid4().hex[:16],
            timestamp=datetime.utcnow().isoformat(),
            backend=type(self._backend).__name__,
            destination=location,
            size_bytes=len(data),
            encrypted=self._encryption,
            compressed=self._compression,
            components=components or [],
        )
        self._records.append(record)
        return record

    async def restore(self, restore_point: RestorePoint, *, destination_namespace: str = "recovery") -> bytes:
        """Restore data from a backup matching the restore point."""
        backup_id = restore_point.backup_id
        if not backup_id and self._records:
            # Find closest backup to requested timestamp
            target = restore_point.timestamp
            backup_id = min(
                self._records,
                key=lambda r: abs(
                    datetime.fromisoformat(r.timestamp).timestamp()
                    - datetime.fromisoformat(target).timestamp()
                ),
            ).id
            # Look up the destination
            for rec in self._records:
                if rec.id == backup_id:
                    backup_id = rec.destination
                    break

        data = await self._backend.retrieve(backup_id)
        if self._compression:
            import zlib

            data = zlib.decompress(data)
        return data

    async def list_backups(self, prefix: str = "") -> list[BackupRecord]:
        return [r for r in self._records if prefix in r.destination]

    async def verify(self, backup_id: str) -> bool:
        """Verify integrity of a backup."""
        for rec in self._records:
            if rec.id == backup_id:
                try:
                    await self._backend.retrieve(rec.destination)
                    rec.verified = True
                    return True
                except Exception:
                    return False
        return False

    @staticmethod
    def register_backend(name: str, cls: type[BaseBackupBackend]) -> None:
        _BACKEND_REGISTRY[name] = cls


# ── Disaster Recovery Testing ────────────────────────────────────────────────


@dataclass
class DRTestResult:
    test_name: str
    timestamp: str
    success: bool
    metrics: dict[str, Any] = field(default_factory=dict)
    error: str = ""


class DRTest:
    """Automated disaster recovery testing framework."""

    def __init__(self) -> None:
        self._results: list[DRTestResult] = []

    async def run_failover_test(
        self,
        failover_chain: FailoverChain,
        *,
        simulate_provider: str,
    ) -> DRTestResult:
        """Simulate a provider failure and verify failover."""
        start = time.time()
        failover_chain.record_failure(simulate_provider)
        # Force circuit open
        for _ in range(10):
            failover_chain.record_failure(simulate_provider)
        active = failover_chain.get_active_provider()
        elapsed = time.time() - start
        success = active != simulate_provider
        result = DRTestResult(
            test_name=f"failover_{simulate_provider}",
            timestamp=datetime.utcnow().isoformat(),
            success=success,
            metrics={
                "failover_seconds": elapsed,
                "active_provider": active,
                "simulated_failure": simulate_provider,
            },
        )
        self._results.append(result)
        # Restore health
        failover_chain.record_success(simulate_provider)
        return result

    async def run_backup_verify_test(self, backup_manager: BackupManager) -> DRTestResult:
        """Verify that all backups are retrievable."""
        all_ok = True
        failed: list[str] = []
        for rec in backup_manager._records:
            ok = await backup_manager.verify(rec.id)
            if not ok:
                all_ok = False
                failed.append(rec.id)
        result = DRTestResult(
            test_name="backup_verification",
            timestamp=datetime.utcnow().isoformat(),
            success=all_ok,
            metrics={"total": len(backup_manager._records), "failed": failed},
        )
        self._results.append(result)
        return result

    def get_results(self) -> list[DRTestResult]:
        return list(self._results)


# ── Chaos Engineering ────────────────────────────────────────────────────────


class ChaosEngineering:
    """Simulate infrastructure failures for resilience testing."""

    def __init__(self) -> None:
        self._active_simulations: dict[str, dict[str, Any]] = {}

    def simulate_failure(
        self,
        *,
        service: str,
        region: str = "",
        failure_type: str = "unavailable",
        duration_seconds: int = 60,
    ) -> str:
        """Start a simulated failure. Returns simulation ID."""
        sim_id = uuid4().hex[:12]
        self._active_simulations[sim_id] = {
            "service": service,
            "region": region,
            "failure_type": failure_type,
            "duration_seconds": duration_seconds,
            "started_at": time.time(),
        }
        return sim_id

    def is_service_affected(self, service: str, region: str = "") -> bool:
        """Check if a service is currently under simulated failure."""
        now = time.time()
        for sim in self._active_simulations.values():
            if sim["service"] == service:
                if region and sim["region"] and sim["region"] != region:
                    continue
                if now - sim["started_at"] < sim["duration_seconds"]:
                    return True
        return False

    def stop_simulation(self, sim_id: str) -> None:
        self._active_simulations.pop(sim_id, None)

    def list_active(self) -> list[dict[str, Any]]:
        now = time.time()
        active: list[dict[str, Any]] = []
        for sid, sim in self._active_simulations.items():
            if now - sim["started_at"] < sim["duration_seconds"]:
                active.append({"id": sid, **sim})
        return active
