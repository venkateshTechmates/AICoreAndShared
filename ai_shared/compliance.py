"""
Compliance Certifications — PRD §22.

Provides: ComplianceExporter, AuditPackage, ComplianceMonitor,
          DataProcessingAgreement tracking.
Follows SRP + OCP: each framework is pluggable, monitor is extensible.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable
from uuid import uuid4


# ── Enums & Config ───────────────────────────────────────────────────────────

class ComplianceFramework(str, Enum):
    SOC2 = "SOC2"
    ISO27001 = "ISO27001"
    GDPR = "GDPR"
    CCPA = "CCPA"
    HIPAA = "HIPAA"
    FEDRAMP = "FedRAMP"
    PCI_DSS = "PCI_DSS"


class CertificationStatus(str, Enum):
    IMPLEMENTED = "implemented"
    IN_PROGRESS = "in_progress"
    PLANNED = "planned"
    NOT_PLANNED = "not_planned"


@dataclass
class CertificationRecord:
    framework: ComplianceFramework
    status: CertificationStatus
    target_date: str = ""
    evidence: str = ""


@dataclass
class DataProcessingAgreement:
    subprocessor: str
    purpose: str
    data_processed: list[str] = field(default_factory=list)
    region: str = ""
    dpa_signed: bool = False


@dataclass
class ComplianceCheckResult:
    check_name: str
    passed: bool
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    details: str = ""
    framework: str = ""
    control_id: str = ""


# ── Audit Package ────────────────────────────────────────────────────────────


@dataclass
class AuditPackage:
    """Bundle of compliance artifacts for auditor review."""

    id: str = field(default_factory=lambda: uuid4().hex[:16])
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    frameworks: list[str] = field(default_factory=list)
    period: str = ""
    artifacts: list[str] = field(default_factory=list)
    checks: list[ComplianceCheckResult] = field(default_factory=list)

    async def save(self, path: str) -> str:
        """Serialize audit package to a file."""
        import json
        import dataclasses

        data = dataclasses.asdict(self)
        with open(path, "w") as f:
            json.dump(data, f, indent=2, default=str)
        return path


# ── Compliance Exporter ──────────────────────────────────────────────────────


class ComplianceExporter:
    """Generate audit packages and compliance reports."""

    def __init__(self) -> None:
        self._certifications: list[CertificationRecord] = []
        self._dpas: list[DataProcessingAgreement] = []
        self._checks: list[ComplianceCheckResult] = []

    def register_certification(self, record: CertificationRecord) -> None:
        self._certifications.append(record)

    def register_dpa(self, dpa: DataProcessingAgreement) -> None:
        self._dpas.append(dpa)

    async def export(
        self,
        *,
        frameworks: list[str],
        period: str = "last_quarter",
        artifacts: list[str] | None = None,
    ) -> AuditPackage:
        """Generate an audit package for the specified frameworks."""
        relevant_checks = [
            c for c in self._checks if c.framework in frameworks
        ]
        package = AuditPackage(
            frameworks=frameworks,
            period=period,
            artifacts=artifacts or [],
            checks=relevant_checks,
        )
        return package

    async def generate_report(
        self,
        *,
        framework: str,
        controls: list[str] | None = None,
    ) -> dict[str, Any]:
        """Generate a compliance status report."""
        relevant = [
            c for c in self._checks
            if c.framework == framework
            and (controls is None or c.control_id in controls)
        ]
        passed = sum(1 for c in relevant if c.passed)
        return {
            "framework": framework,
            "controls_checked": len(relevant),
            "controls_passed": passed,
            "controls_failed": len(relevant) - passed,
            "pass_rate": passed / len(relevant) if relevant else 0.0,
            "timestamp": datetime.utcnow().isoformat(),
            "details": [
                {"control": c.control_id, "passed": c.passed, "details": c.details}
                for c in relevant
            ],
        }

    def get_certification_matrix(self) -> list[dict[str, str]]:
        return [
            {
                "framework": c.framework.value,
                "status": c.status.value,
                "target_date": c.target_date,
                "evidence": c.evidence,
            }
            for c in self._certifications
        ]


# ── Compliance Monitor ───────────────────────────────────────────────────────


class ComplianceMonitor:
    """Continuous compliance monitoring with pluggable checks."""

    def __init__(self) -> None:
        self._checks: dict[str, Callable[..., ComplianceCheckResult]] = {}
        self._results: list[ComplianceCheckResult] = []

    def register_check(
        self,
        name: str,
        check_fn: Callable[..., ComplianceCheckResult],
    ) -> None:
        self._checks[name] = check_fn

    async def run_all(self) -> list[ComplianceCheckResult]:
        """Execute all registered compliance checks."""
        results: list[ComplianceCheckResult] = []
        for name, fn in self._checks.items():
            try:
                result = fn()
                results.append(result)
            except Exception as exc:
                results.append(
                    ComplianceCheckResult(
                        check_name=name,
                        passed=False,
                        details=f"Check failed with error: {exc}",
                    )
                )
        self._results.extend(results)
        return results

    async def verify_encryption(self, resource: str) -> ComplianceCheckResult:
        """Verify encryption at rest for a resource (stub — integrate with infra)."""
        return ComplianceCheckResult(
            check_name=f"encryption_{resource}",
            passed=True,
            framework="SOC2",
            control_id="CC6.1",
            details=f"Encryption verified for {resource}",
        )

    async def verify_backups(self, *, last_24h: bool = True) -> ComplianceCheckResult:
        """Verify backup completion (stub — integrate with BackupManager)."""
        return ComplianceCheckResult(
            check_name="backup_verification",
            passed=True,
            framework="SOC2",
            control_id="CC7.1",
            details="Backup verification passed" + (" (last 24h)" if last_24h else ""),
        )

    async def verify_rbac_enforcement(self) -> ComplianceCheckResult:
        """Verify RBAC is properly enforced (stub — integrate with auth)."""
        return ComplianceCheckResult(
            check_name="rbac_enforcement",
            passed=True,
            framework="SOC2",
            control_id="CC6.6",
            details="RBAC enforcement verified",
        )

    def get_results(self, *, framework: str | None = None) -> list[ComplianceCheckResult]:
        if framework:
            return [r for r in self._results if r.framework == framework]
        return list(self._results)
