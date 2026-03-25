"""
Tests for ai_shared.compliance — ComplianceMonitor, ComplianceExporter, AuditPackage.
"""

from __future__ import annotations

import asyncio

import pytest

from ai_shared.compliance import (
    AuditPackage,
    CertificationRecord,
    CertificationStatus,
    ComplianceCheckResult,
    ComplianceExporter,
    ComplianceFramework,
    ComplianceMonitor,
)


# ── ComplianceMonitor ─────────────────────────────────────────────────────────


class TestComplianceMonitor:
    def setup_method(self):
        self.monitor = ComplianceMonitor()

    @pytest.mark.asyncio
    async def test_register_and_run_check(self):
        self.monitor.register_check(
            "test_check",
            lambda: ComplianceCheckResult(check_name="test_check", passed=True, framework="SOC2"),
        )
        results = await self.monitor.run_all()
        assert len(results) == 1
        assert results[0].passed is True

    @pytest.mark.asyncio
    async def test_failing_check_recorded(self):
        self.monitor.register_check(
            "bad_check",
            lambda: ComplianceCheckResult(check_name="bad_check", passed=False),
        )
        results = await self.monitor.run_all()
        assert results[0].passed is False

    @pytest.mark.asyncio
    async def test_exception_in_check_captured(self):
        def boom():
            raise RuntimeError("Check exploded")
        self.monitor.register_check("boom", boom)
        results = await self.monitor.run_all()
        assert len(results) == 1
        assert results[0].passed is False
        assert "error" in results[0].details.lower()

    @pytest.mark.asyncio
    async def test_verify_encryption_true(self):
        result = await self.monitor.verify_encryption("data_store", encrypted=True)
        assert result.passed is True
        assert result.framework == "SOC2"

    @pytest.mark.asyncio
    async def test_verify_encryption_false(self):
        result = await self.monitor.verify_encryption("data_store", encrypted=False)
        assert result.passed is False

    @pytest.mark.asyncio
    async def test_verify_backups_with_count(self):
        result = await self.monitor.verify_backups(backup_count=3)
        assert result.passed is True

    @pytest.mark.asyncio
    async def test_verify_backups_zero_count(self):
        result = await self.monitor.verify_backups(backup_count=0)
        assert result.passed is False

    @pytest.mark.asyncio
    async def test_verify_rbac_configured(self):
        result = await self.monitor.verify_rbac_enforcement(roles_configured=5)
        assert result.passed is True

    @pytest.mark.asyncio
    async def test_verify_rbac_not_configured(self):
        result = await self.monitor.verify_rbac_enforcement(roles_configured=0)
        assert result.passed is False

    @pytest.mark.asyncio
    async def test_verify_hipaa_phi_enabled(self):
        result = await self.monitor.verify_hipaa_phi_protection(pii_detector_enabled=True)
        assert result.passed is True
        assert result.framework == "HIPAA"

    @pytest.mark.asyncio
    async def test_verify_hipaa_phi_disabled(self):
        result = await self.monitor.verify_hipaa_phi_protection(pii_detector_enabled=False)
        assert result.passed is False

    @pytest.mark.asyncio
    async def test_verify_gdpr_consent(self):
        result = await self.monitor.verify_gdpr_consent(consent_records=100)
        assert result.passed is True
        assert result.framework == "GDPR"

    @pytest.mark.asyncio
    async def test_verify_gdpr_consent_zero(self):
        result = await self.monitor.verify_gdpr_consent(consent_records=0)
        assert result.passed is False

    @pytest.mark.asyncio
    async def test_verify_audit_logging(self):
        result = await self.monitor.verify_audit_logging(log_entries=50)
        assert result.passed is True

    @pytest.mark.asyncio
    async def test_verify_data_retention(self):
        result = await self.monitor.verify_data_retention(policies_configured=3)
        assert result.passed is True

    def test_get_results_by_framework(self):
        self.monitor._results = [
            ComplianceCheckResult(check_name="a", passed=True, framework="SOC2"),
            ComplianceCheckResult(check_name="b", passed=True, framework="HIPAA"),
        ]
        soc2 = self.monitor.get_results(framework="SOC2")
        assert len(soc2) == 1
        assert soc2[0].framework == "SOC2"


# ── ComplianceExporter ────────────────────────────────────────────────────────


class TestComplianceExporter:
    def setup_method(self):
        self.exporter = ComplianceExporter()

    def test_register_certification(self):
        self.exporter.register_certification(CertificationRecord(
            framework=ComplianceFramework.HIPAA,
            status=CertificationStatus.IMPLEMENTED,
        ))
        matrix = self.exporter.get_certification_matrix()
        assert len(matrix) == 1
        assert matrix[0]["framework"] == "HIPAA"
        assert matrix[0]["status"] == "implemented"

    @pytest.mark.asyncio
    async def test_export_creates_package(self):
        package = await self.exporter.export(frameworks=["SOC2", "HIPAA"], period="Q1_2026")
        assert isinstance(package, AuditPackage)
        assert "SOC2" in package.frameworks
        assert package.period == "Q1_2026"

    @pytest.mark.asyncio
    async def test_generate_report_empty(self):
        report = await self.exporter.generate_report(framework="SOC2")
        assert report["controls_checked"] == 0
        assert report["pass_rate"] == 0.0

    @pytest.mark.asyncio
    async def test_generate_report_with_checks(self):
        self.exporter._checks = [
            ComplianceCheckResult(check_name="a", passed=True, framework="SOC2", control_id="CC6.1"),
            ComplianceCheckResult(check_name="b", passed=False, framework="SOC2", control_id="CC6.6"),
            ComplianceCheckResult(check_name="c", passed=True, framework="HIPAA", control_id="164.312"),
        ]
        report = await self.exporter.generate_report(framework="SOC2")
        assert report["controls_checked"] == 2
        assert report["controls_passed"] == 1
        assert report["pass_rate"] == 0.5

    def test_multiple_certifications(self):
        for fw in [ComplianceFramework.SOC2, ComplianceFramework.GDPR, ComplianceFramework.HIPAA]:
            self.exporter.register_certification(CertificationRecord(
                framework=fw, status=CertificationStatus.IMPLEMENTED,
            ))
        matrix = self.exporter.get_certification_matrix()
        assert len(matrix) == 3
