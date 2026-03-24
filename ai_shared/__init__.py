"""
AI Shared Library — Enterprise utilities for the AI Core framework.

Provides: memory, observability, tokens, caching, security, auth,
          resilience, plugins, logging, governance, cost, models,
          experiments, compliance.
"""

__version__ = "1.1.0"

from ai_shared.memory import (
    BaseMemory,
    ConversationBufferMemory,
    ConversationSummaryMemory,
    VectorMemory,
    RedisMemory,
    PostgresMemory,
    EntityMemory,
    MemoryFactory,
)
from ai_shared.observability import Tracer, Span, Trace, get_tracer, trace, MetricsCollector, metrics
from ai_shared.tokens import TokenBudget, BudgetStrategy, count_tokens, estimate_cost
from ai_shared.cache import BaseCache, ExactCache, SemanticCache, RedisCache, MultiLayerCache
from ai_shared.security import PIIDetector, ContentFilter, InputValidator
from ai_shared.auth import AuthManager, RBAC, JWTValidator, APIKeyManager, Permission, User
from ai_shared.resilience import retry, RetryConfig, CircuitBreaker, RateLimiter, with_timeout
from ai_shared.plugins import PluginRegistry, PluginMetadata, plugin
from ai_shared.logging_utils import get_logger, LogContext, log_execution
from ai_shared.governance import (
    DataLineageTracker, DataClassifier, PolicyEngine, AuditLogger,
    RetentionManager, RetentionPolicy, GDPRManager,
)
from ai_shared.cost import CostTracker, CostOptimizer, QuotaManager, QuotaConfig
from ai_shared.models import ModelRegistry, ABTestingFramework, RollbackManager
from ai_shared.experiments import ExperimentManager, FeatureFlags, ExperimentAnalytics
from ai_shared.compliance import (
    ComplianceExporter, ComplianceMonitor, AuditPackage,
    ComplianceFramework, CertificationStatus, CertificationRecord,
)

__all__ = [
    # Memory
    "BaseMemory", "ConversationBufferMemory", "ConversationSummaryMemory",
    "VectorMemory", "RedisMemory", "PostgresMemory", "EntityMemory", "MemoryFactory",
    # Observability
    "Tracer", "Span", "Trace", "get_tracer", "trace", "MetricsCollector", "metrics",
    # Tokens
    "TokenBudget", "BudgetStrategy", "count_tokens", "estimate_cost",
    # Cache
    "BaseCache", "ExactCache", "SemanticCache", "RedisCache", "MultiLayerCache",
    # Security
    "PIIDetector", "ContentFilter", "InputValidator",
    # Auth
    "AuthManager", "RBAC", "JWTValidator", "APIKeyManager", "Permission", "User",
    # Resilience
    "retry", "RetryConfig", "CircuitBreaker", "RateLimiter", "with_timeout",
    # Plugins
    "PluginRegistry", "PluginMetadata", "plugin",
    # Logging
    "get_logger", "LogContext", "log_execution",
    # Governance
    "DataLineageTracker", "DataClassifier", "PolicyEngine", "AuditLogger",
    "RetentionManager", "RetentionPolicy", "GDPRManager",
    # Cost
    "CostTracker", "CostOptimizer", "QuotaManager", "QuotaConfig",
    # Models
    "ModelRegistry", "ABTestingFramework", "RollbackManager",
    # Experiments
    "ExperimentManager", "FeatureFlags", "ExperimentAnalytics",
    # Compliance
    "ComplianceExporter", "ComplianceMonitor", "AuditPackage",
    "ComplianceFramework", "CertificationStatus", "CertificationRecord",
]
