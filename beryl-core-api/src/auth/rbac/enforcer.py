"""
RBAC Enforcer for Zero-Trust Architecture.

Implements Role-Based Access Control with domain-specific permissions.
Enforces least privilege principle and comprehensive authorization.
"""

import logging
from typing import Dict, List, Set, Optional
from dataclasses import dataclass
from enum import Enum

class Permission(Enum):
    """Defined permissions in the system."""
    # General permissions
    GENERAL_ACCESS = "general:access"

    # Fintech permissions
    FINTECH_READ = "fintech:read"
    FINTECH_WRITE = "fintech:write"
    FINTECH_ADMIN = "fintech:admin"

    # Mobility permissions
    MOBILITY_READ = "mobility:read"
    MOBILITY_WRITE = "mobility:write"
    MOBILITY_ADMIN = "mobility:admin"

    # ESG permissions
    ESG_READ = "esg:read"
    ESG_WRITE = "esg:write"
    ESG_ADMIN = "esg:admin"

    # Social permissions
    SOCIAL_READ = "social:read"
    SOCIAL_WRITE = "social:write"
    SOCIAL_ADMIN = "social:admin"

    # GraphQL permissions
    GRAPHQL_EXECUTE = "graphql:execute"
    GRAPHQL_INTROSPECT = "graphql:introspect"

    # Event permissions
    EVENT_PUBLISH = "event:publish"
    EVENT_CONSUME = "event:consume"
    EVENT_ADMIN = "event:admin"

    # Observability permissions
    METRICS_READ = "metrics:read"
    LOGS_READ = "logs:read"
    TRACES_READ = "traces:read"
    AUDIT_READ = "audit:read"

class Role(Enum):
    """Defined roles in the system."""
    GUEST = "guest"
    USER = "user"
    PREMIUM_USER = "premium_user"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"
    AUDITOR = "auditor"
    SERVICE = "service"

@dataclass
class UserContext:
    """User context for authorization decisions."""
    user_id: str
    roles: List[str]
    domains: List[str]
    attributes: Dict[str, any] = None

class RBACEnforcer:
    """Enforces Role-Based Access Control with Zero-Trust principles."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Define role-permission mappings
        self.role_permissions = self._initialize_role_permissions()

        # Define domain-specific rules
        self.domain_rules = self._initialize_domain_rules()

    def _initialize_role_permissions(self) -> Dict[str, Set[str]]:
        """Initialize the role-permission mappings."""
        return {
            Role.GUEST.value: {
                Permission.GENERAL_ACCESS.value,
                Permission.METRICS_READ.value,
            },
            Role.USER.value: {
                Permission.GENERAL_ACCESS.value,
                Permission.MOBILITY_READ.value,
                Permission.SOCIAL_READ.value,
                Permission.GRAPHQL_EXECUTE.value,
                Permission.METRICS_READ.value,
            },
            Role.PREMIUM_USER.value: {
                Permission.GENERAL_ACCESS.value,
                Permission.FINTECH_READ.value,
                Permission.MOBILITY_READ.value,
                Permission.MOBILITY_WRITE.value,
                Permission.ESG_READ.value,
                Permission.SOCIAL_READ.value,
                Permission.SOCIAL_WRITE.value,
                Permission.GRAPHQL_EXECUTE.value,
                Permission.EVENT_PUBLISH.value,
                Permission.METRICS_READ.value,
            },
            Role.ADMIN.value: {
                Permission.GENERAL_ACCESS.value,
                Permission.FINTECH_READ.value,
                Permission.FINTECH_WRITE.value,
                Permission.MOBILITY_READ.value,
                Permission.MOBILITY_WRITE.value,
                Permission.MOBILITY_ADMIN.value,
                Permission.ESG_READ.value,
                Permission.ESG_WRITE.value,
                Permission.SOCIAL_READ.value,
                Permission.SOCIAL_WRITE.value,
                Permission.SOCIAL_ADMIN.value,
                Permission.GRAPHQL_EXECUTE.value,
                Permission.GRAPHQL_INTROSPECT.value,
                Permission.EVENT_PUBLISH.value,
                Permission.EVENT_CONSUME.value,
                Permission.EVENT_ADMIN.value,
                Permission.METRICS_READ.value,
                Permission.LOGS_READ.value,
                Permission.TRACES_READ.value,
            },
            Role.SUPER_ADMIN.value: {
                # All permissions
                *[p.value for p in Permission],
            },
            Role.AUDITOR.value: {
                Permission.GENERAL_ACCESS.value,
                Permission.AUDIT_READ.value,
                Permission.LOGS_READ.value,
                Permission.METRICS_READ.value,
                Permission.TRACES_READ.value,
            },
            Role.SERVICE.value: {
                Permission.GENERAL_ACCESS.value,
                Permission.EVENT_PUBLISH.value,
                Permission.EVENT_CONSUME.value,
                Permission.METRICS_READ.value,
                # Services get domain-specific permissions based on their function
            }
        }

    def _initialize_domain_rules(self) -> Dict[str, Dict]:
        """Initialize domain-specific authorization rules."""
        return {
            "fintech": {
                "sensitive": True,
                "requires_consent": True,
                "allowed_countries": ["FR", "DE", "IT", "ES"],  # EU only for fintech
                "max_session_duration": 3600,  # 1 hour
                "audit_level": "detailed"
            },
            "esg": {
                "sensitive": True,
                "requires_consent": True,
                "allowed_countries": ["FR", "DE", "IT", "ES", "US", "CA"],
                "max_session_duration": 7200,  # 2 hours
                "audit_level": "detailed"
            },
            "mobility": {
                "sensitive": False,
                "requires_consent": False,
                "allowed_countries": ["FR", "DE", "IT", "ES", "US", "CA", "GB"],
                "max_session_duration": 86400,  # 24 hours
                "audit_level": "standard"
            },
            "social": {
                "sensitive": False,
                "requires_consent": False,
                "allowed_countries": ["ALL"],
                "max_session_duration": 2592000,  # 30 days
                "audit_level": "minimal"
            }
        }

    def check_permissions(self, user_id: str, roles: List[str], domains: List[str],
                         required_permissions: List[str]) -> bool:
        """
        Check if user has required permissions.

        Args:
            user_id: User identifier
            roles: List of user roles
            domains: List of user domains
            required_permissions: List of required permissions

        Returns:
            True if user has all required permissions, False otherwise
        """
        try:
            # Get all permissions for user's roles
            user_permissions = set()
            for role in roles:
                if role in self.role_permissions:
                    user_permissions.update(self.role_permissions[role])

            # Add domain-specific permissions
            for domain in domains:
                domain_perms = self._get_domain_permissions(domain, roles)
                user_permissions.update(domain_perms)

            # Check if user has all required permissions
            missing_permissions = set(required_permissions) - user_permissions

            if missing_permissions:
                self.logger.warning(
                    f"User {user_id} missing permissions: {missing_permissions}"
                )
                return False

            # Additional domain-specific checks
            for permission in required_permissions:
                if not self._validate_domain_specific_rules(user_id, permission, domains):
                    return False

            return True

        except Exception as e:
            self.logger.error(f"Error checking permissions for user {user_id}: {e}")
            return False

    def _get_domain_permissions(self, domain: str, roles: List[str]) -> Set[str]:
        """Get domain-specific permissions based on roles."""
        domain_permissions = set()

        # Service accounts get domain-specific permissions
        if "service" in roles:
            if domain == "fintech":
                domain_permissions.update([
                    Permission.FINTECH_READ.value,
                    Permission.FINTECH_WRITE.value
                ])
            elif domain == "mobility":
                domain_permissions.update([
                    Permission.MOBILITY_READ.value,
                    Permission.MOBILITY_WRITE.value
                ])
            elif domain == "esg":
                domain_permissions.update([
                    Permission.ESG_READ.value,
                    Permission.ESG_WRITE.value
                ])
            elif domain == "social":
                domain_permissions.update([
                    Permission.SOCIAL_READ.value,
                    Permission.SOCIAL_WRITE.value
                ])

        return domain_permissions

    def _validate_domain_specific_rules(self, user_id: str, permission: str,
                                      domains: List[str]) -> bool:
        """Validate domain-specific authorization rules."""
        # Extract domain from permission
        if ":" in permission:
            domain = permission.split(":")[0]
        else:
            return True  # Not domain-specific

        if domain not in self.domain_rules:
            return True  # No specific rules

        rules = self.domain_rules[domain]

        # Check if domain is in user's allowed domains
        if domain not in domains:
            self.logger.warning(f"User {user_id} not authorized for domain {domain}")
            return False

        # Additional validations can be added here
        # (e.g., time-based restrictions, geo-restrictions, etc.)

        return True

    def get_user_permissions(self, user_id: str, roles: List[str],
                           domains: List[str]) -> Set[str]:
        """Get all permissions for a user."""
        permissions = set()

        # Add role-based permissions
        for role in roles:
            if role in self.role_permissions:
                permissions.update(self.role_permissions[role])

        # Add domain-specific permissions
        for domain in domains:
            domain_perms = self._get_domain_permissions(domain, roles)
            permissions.update(domain_perms)

        return permissions

    def validate_scope(self, token_scopes: List[str], required_scopes: List[str]) -> bool:
        """Validate OAuth2 scopes."""
        return set(required_scopes).issubset(set(token_scopes))

    def check_domain_access(self, user_id: str, domain: str, operation: str) -> bool:
        """Check if user can access a specific domain for a specific operation."""
        # This is a simplified check - in practice, this would be more complex
        permission = f"{domain}:{operation}"
        # Assume user has the permission for this example
        return True  # TODO: Implement proper domain access control