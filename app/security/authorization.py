from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from app.security.context import SecurityContext


class ActionRisk(str, Enum):
    READ = "read"
    LOW_MUTATION = "low_mutation"
    HIGH_MUTATION = "high_mutation"


@dataclass(frozen=True)
class ToolPolicy:
    action: str
    risk: ActionRisk
    allowed_roles: frozenset[str]
    requires_customer_mapping: bool = False
    requires_resource_ownership: bool = False
    requires_confirmation: bool = False


TOOL_POLICIES: dict[str, ToolPolicy] = {
    "search_products": ToolPolicy("search_products", ActionRisk.READ, frozenset({"customer", "support", "admin"})),
    "check_inventory": ToolPolicy("check_inventory", ActionRisk.READ, frozenset({"customer", "support", "admin"})),
    "search_knowledge": ToolPolicy("search_knowledge", ActionRisk.READ, frozenset({"customer", "support", "admin"})),
    "create_cart": ToolPolicy("create_cart", ActionRisk.LOW_MUTATION, frozenset({"customer", "admin"})),
    "get_cart": ToolPolicy("get_cart", ActionRisk.READ, frozenset({"customer", "admin"})),
    "add_to_cart": ToolPolicy("add_to_cart", ActionRisk.LOW_MUTATION, frozenset({"customer", "admin"})),
    "update_quantity": ToolPolicy("update_quantity", ActionRisk.LOW_MUTATION, frozenset({"customer", "admin"})),
    "remove_from_cart": ToolPolicy("remove_from_cart", ActionRisk.LOW_MUTATION, frozenset({"customer", "admin"})),
    "calculate_cart": ToolPolicy("calculate_cart", ActionRisk.READ, frozenset({"customer", "admin"})),
    "apply_discount_code": ToolPolicy("apply_discount_code", ActionRisk.LOW_MUTATION, frozenset({"customer", "admin"})),
    "lookup_order": ToolPolicy("lookup_order", ActionRisk.READ, frozenset({"customer", "support", "admin"}), True, True),
    "get_order_status": ToolPolicy("get_order_status", ActionRisk.READ, frozenset({"customer", "support", "admin"}), True, True),
    "get_order_details": ToolPolicy("get_order_details", ActionRisk.READ, frozenset({"customer", "support", "admin"}), True, True),
    "get_order_history": ToolPolicy("get_order_history", ActionRisk.READ, frozenset({"customer", "support", "admin"}), True, False),
    "check_order_cancellation_eligibility": ToolPolicy("check_order_cancellation_eligibility", ActionRisk.READ, frozenset({"customer", "support", "admin"}), True, True),
    "check_order_return_eligibility": ToolPolicy("check_order_return_eligibility", ActionRisk.READ, frozenset({"customer", "support", "admin"}), True, True),
    # Phase 5C will implement these mutations with HITL.
    "cancel_order": ToolPolicy("cancel_order", ActionRisk.HIGH_MUTATION, frozenset({"customer", "admin"}), True, True, True),
    "create_return": ToolPolicy("create_return", ActionRisk.HIGH_MUTATION, frozenset({"customer", "admin"}), True, True, True),
}


class AuthorizationService:
    @staticmethod
    def authorize_tool(
        context: SecurityContext,
        action: str,
        *,
        resource_shopify_customer_id: str | None = None,
        confirmed: bool = False,
    ) -> ToolPolicy:
        if not context.is_authenticated:
            raise PermissionError("Authentication is required for this action.")

        policy = TOOL_POLICIES.get(action)
        if policy is None:
            raise PermissionError(f"Tool/action '{action}' is not allowlisted.")

        if not any(role in policy.allowed_roles for role in context.roles):
            raise PermissionError("You are not authorized to perform this action.")

        if policy.requires_customer_mapping and not context.shopify_customer_id:
            raise PermissionError("A Shopify customer identity mapping is required for this action.")

        if policy.requires_resource_ownership:
            if not resource_shopify_customer_id:
                raise PermissionError("The requested resource has no customer owner and cannot be accessed.")
            if context.has_role("admin"):
                pass
            elif context.has_role("support"):
                # Support access can be narrowed further when enterprise RBAC is added.
                pass
            elif resource_shopify_customer_id != context.shopify_customer_id:
                raise PermissionError("The requested order does not belong to the authenticated customer.")

        if policy.requires_confirmation and not confirmed:
            raise PermissionError("Explicit confirmation is required for this high-impact action.")

        return policy
