import pytest

from app.clients.shopify_cart_client import ShopifyCartClient
from app.graph.commerce_graph import commerce_graph


# ============================================================
# TEST HELPERS
# ============================================================

def invoke_commerce_graph(
    message: str,
    cart_id: str,
) -> dict:
    """
    Invoke the LangGraph commerce workflow using
    the same Shopify cart across multiple requests.
    """

    print("\n")
    print("=" * 80)
    print(f"USER MESSAGE: {message}")
    print("=" * 80)

    result = commerce_graph.invoke(
        {
            "user_message": message,
            "cart_id": cart_id,
            "intent": "unknown",
            "cart_action": "unknown",
            "cart_changed": False,
            "response": "",
            "error": None,
        }
    )

    print("\nGRAPH RESULT")
    print("-" * 80)

    print(f"Intent       : {result.get('intent')}")
    print(f"Cart Action  : {result.get('cart_action')}")
    print(f"Cart Changed : {result.get('cart_changed')}")
    print(f"Error        : {result.get('error')}")
    print(f"Response     : {result.get('response')}")

    print("-" * 80)

    return result


# ============================================================
# END-TO-END CART WORKFLOW TEST
# ============================================================

def test_cart_add_update_view_workflow():
    """
    Test complete LangGraph cart workflow:

    1. Create a fresh Shopify cart
    2. Add Athletic Running Shoes US 8 / Black
    3. Change line 1 quantity to 3
    4. Show cart
    5. Verify Shopify cart really contains quantity 3

    This is an integration test.
    It calls:
        - LangGraph
        - LLM for extraction, if used by graph nodes
        - Shopify Admin/Storefront APIs
    """

    # ========================================================
    # STEP 0 — CREATE FRESH SHOPIFY CART
    # ========================================================

    cart_client = ShopifyCartClient()

    cart = cart_client.create_cart()

    assert cart is not None, (
        "Shopify create_cart() returned None."
    )

    assert "id" in cart, (
        f"Shopify create_cart() did not return cart id. "
        f"Response: {cart}"
    )

    cart_id = cart["id"]

    assert cart_id, (
        "Shopify cart ID is empty."
    )

    print("\n")
    print("=" * 80)
    print("FRESH SHOPIFY CART CREATED")
    print("=" * 80)

    # Do NOT log the complete cart ID because Shopify
    # cart IDs may contain a sensitive ?key= value.
    print(f"Cart ID present: {bool(cart_id)}")
    print(f"Initial quantity: {cart.get('totalQuantity')}")

    # ========================================================
    # STEP 1 — ADD PRODUCT
    # ========================================================

    add_result = invoke_commerce_graph(
        message=(
            "Add Athletic Running Shoes "
            "US 8 / Black to my cart"
        ),
        cart_id=cart_id,
    )

    # Verify routing
    assert add_result.get("intent") == "cart", (
        f"Expected intent='cart', "
        f"got {add_result.get('intent')}"
    )

    assert add_result.get("cart_action") == "add", (
        f"Expected cart_action='add', "
        f"got {add_result.get('cart_action')}"
    )

    # Verify graph completed successfully
    assert not add_result.get("error"), (
        f"Add workflow failed: "
        f"{add_result.get('error')}"
    )

    assert add_result.get("cart_changed") is True, (
        "Add workflow should set cart_changed=True."
    )

    assert add_result.get("response"), (
        "Add workflow returned an empty response."
    )

    print("\n✅ STEP 1 PASSED — PRODUCT ADDED")

    # ========================================================
    # VERIFY SHOPIFY AFTER ADD
    # ========================================================

    cart_after_add = cart_client.get_cart(
        cart_id
    )

    print("\nSHOPIFY CART AFTER ADD")
    print(cart_after_add)

    assert cart_after_add is not None

    assert cart_after_add.get("totalQuantity") == 1, (
        "Expected Shopify totalQuantity=1 after add, "
        f"got {cart_after_add.get('totalQuantity')}"
    )

    # ========================================================
    # STEP 2 — CHANGE LINE 1 QUANTITY TO 3
    # ========================================================

    update_result = invoke_commerce_graph(
        message="Change line 1 quantity to 3",
        cart_id=cart_id,
    )

    # Verify routing
    assert update_result.get("intent") == "cart", (
        f"Expected intent='cart', "
        f"got {update_result.get('intent')}"
    )

    assert update_result.get("cart_action") == "update", (
        f"Expected cart_action='update', "
        f"got {update_result.get('cart_action')}"
    )

    # Verify graph completed successfully
    assert not update_result.get("error"), (
        f"Update workflow failed: "
        f"{update_result.get('error')}"
    )

    assert update_result.get("cart_changed") is True, (
        "Update workflow should set cart_changed=True."
    )

    assert update_result.get("response"), (
        "Update workflow returned an empty response."
    )

    print("\n✅ STEP 2 PASSED — QUANTITY UPDATED")

    # ========================================================
    # VERIFY SHOPIFY AFTER UPDATE
    # ========================================================

    cart_after_update = cart_client.get_cart(
        cart_id
    )

    print("\nSHOPIFY CART AFTER QUANTITY UPDATE")
    print(cart_after_update)

    assert cart_after_update is not None

    assert cart_after_update.get("totalQuantity") == 3, (
        "Expected Shopify totalQuantity=3 after update, "
        f"got {cart_after_update.get('totalQuantity')}"
    )

    # ========================================================
    # STEP 3 — SHOW CART
    # ========================================================

    view_result = invoke_commerce_graph(
        message="Show me my cart",
        cart_id=cart_id,
    )

    # Verify routing
    assert view_result.get("intent") == "cart", (
        f"Expected intent='cart', "
        f"got {view_result.get('intent')}"
    )

    assert view_result.get("cart_action") == "view", (
        f"Expected cart_action='view', "
        f"got {view_result.get('cart_action')}"
    )

    # Viewing must not mutate the cart
    assert view_result.get("cart_changed") is False, (
        "Viewing cart should not change the cart."
    )

    assert not view_result.get("error"), (
        f"View cart workflow failed: "
        f"{view_result.get('error')}"
    )

    response = view_result.get("response")

    assert response, (
        "View cart returned empty response."
    )

    print("\nFINAL CART RESPONSE")
    print("=" * 80)
    print(response)
    print("=" * 80)

    # ========================================================
    # VERIFY USER-FACING RESPONSE
    # ========================================================

    assert "Athletic Running Shoes" in response, (
        "Final cart response does not contain "
        "'Athletic Running Shoes'."
    )

    # Allow different formatter wording.
    quantity_found = any(
        value.lower() in response.lower()
        for value in [
            "qty: 3",
            "qty 3",
            "quantity: 3",
            "quantity 3",
            "3 ×",
            "3 x",
        ]
    )

    assert quantity_found, (
        "Final cart response does not appear "
        "to show quantity 3.\n"
        f"Actual response:\n{response}"
    )

    # ========================================================
    # FINAL SHOPIFY VERIFICATION
    # ========================================================

    final_cart = cart_client.get_cart(
        cart_id
    )

    assert final_cart.get("totalQuantity") == 3

    lines = (
        final_cart
        .get("lines", {})
        .get("nodes", [])
    )

    assert len(lines) == 1, (
        f"Expected exactly 1 cart line, "
        f"found {len(lines)}."
    )

    line = lines[0]

    assert line.get("quantity") == 3, (
        f"Expected line quantity=3, "
        f"got {line.get('quantity')}"
    )

    merchandise = line.get(
        "merchandise",
        {}
    )

    product = merchandise.get(
        "product",
        {}
    )

    assert (
        product.get("title")
        == "Athletic Running Shoes"
    ), (
        "Unexpected product in final Shopify cart: "
        f"{product.get('title')}"
    )

    assert (
        merchandise.get("title")
        == "US 8 / Black"
    ), (
        "Unexpected variant in final Shopify cart: "
        f"{merchandise.get('title')}"
    )

    print("\n")
    print("=" * 80)
    print("✅ COMPLETE LANGGRAPH CART WORKFLOW PASSED")
    print("=" * 80)
    print("1. ADD PRODUCT       ✅")
    print("2. UPDATE QUANTITY   ✅")
    print("3. VIEW CART         ✅")
    print("4. SHOPIFY VERIFIED  ✅")
    print("=" * 80)