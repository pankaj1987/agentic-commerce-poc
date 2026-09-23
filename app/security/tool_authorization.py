from app.security.authorization import AuthorizationService
from app.security.context import get_current_security_context


def authorize_current_tool(
    action: str,
    *,
    resource_shopify_customer_id: str | None = None,
    confirmed: bool = False,
):
    context = get_current_security_context(required=True)
    return AuthorizationService.authorize_tool(
        context,
        action,
        resource_shopify_customer_id=resource_shopify_customer_id,
        confirmed=confirmed,
    )
