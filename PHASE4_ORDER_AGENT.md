# Phase 4 - Order Agent

## Scope

Implemented:
- Order Agent integrated into the existing LangGraph domain graph.
- Order lookup by Shopify order name/number.
- Order status, fulfillment, delivery and tracking details.
- Order details and line items.
- Recent order history by customer email.
- Read-only cancellation eligibility facts.
- Read-only return eligibility combining Shopify facts with RAG return policy.
- Direct REST endpoints for deterministic testing.
- Planner/router support for `order` intent and mixed order + knowledge prompts.
- One structured-planner retry for local-model JSON failures.

Not implemented intentionally in Phase 4:
- `orderCancel` mutation.
- `returnRequest` / `returnCreate` mutation.
- Refund execution.
- Checkout/payment.

Those writes should be enabled after Phase 5 confirmation/HITL, guardrails, idempotency and security.

## Shopify scopes

Minimum for this Phase 4 implementation:
- `read_orders`

Shopify normally exposes only the last 60 days of orders to apps. Older order history requires Shopify approval/access for all orders (`read_all_orders` in addition to normal order access).

When Phase 5 enables mutations, additional scopes will be required, including `write_orders` for cancellation and `write_returns` for return workflows.

## Direct API tests

- `GET /api/orders/%231001`
- `GET /api/orders?customer_email=test@example.com&limit=10`
- `GET /api/orders/%231001/cancellation-eligibility`
- `GET /api/orders/%231001/return-eligibility`

In Swagger, enter `#1001` as the path value; URL encoding is handled by the client.

## Chat tests

1. `Where is order #1001?`
2. `Show me the status of order #1001.`
3. `Show all details for order #1001.`
4. `What items are in order #1001?`
5. `Show my recent orders for test@example.com.`
6. `Can I cancel order #1001?`
7. `Can I return the running shoes from order #1001?`
8. `Show details for order #1001 and tell me the return policy.`
9. Conversation: `Show order #1001.` then `Has it shipped?`
10. Conversation: `Show order #1001.` then `Can I return the shoes from it?`

## Security note

Order-history lookup currently requires an explicit email because the current POC has no authenticated mapping from application user/session to Shopify customer. Do not change `my orders` to return store-wide orders. Phase 5 should bind an authenticated application user to a Shopify customer identity and enforce ownership before exposing order data.
