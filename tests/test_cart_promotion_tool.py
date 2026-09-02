from app.clients.shopify_cart_client import ShopifyCartClient
from app.tools.cart_tools import apply_promotion


def test_apply_discount_code():
    client = ShopifyCartClient()

    # 1. Create cart
    created_cart = client.create_cart()
    cart_id = created_cart["id"]

    print("\n========== CREATED CART ==========")
    print(created_cart)

    # 2. Apply promotion
    result = client.apply_discount_code(
        cart_id=cart_id,
        discount_code="SAVE20",
    )

    print("\n========== PROMOTION RESULT ==========")
    print(result)

    assert result is not None
    assert "cart" in result
    assert "user_errors" in result
    assert "warnings" in result


def test_apply_promotion_tool():
    client = ShopifyCartClient()

    created_cart = client.create_cart()
    cart_id = created_cart["id"]

    result = apply_promotion.invoke(
        {
            "cart_id": cart_id,
            "discount_code": "6ARH7B1F6YN9",
        }
    )

    print("\n========== APPLY PROMOTION TOOL ==========")
    print(result)

    assert result is not None
    assert "status" in result


def test_invalid_promotion():
    client = ShopifyCartClient()

    created_cart = client.create_cart()
    cart_id = created_cart["id"]

    result = apply_promotion.invoke(
        {
            "cart_id": cart_id,
            "discount_code": "INVALID_CODE_12345",
        }
    )

    print("\n========== INVALID PROMOTION ==========")
    print(result)

    assert result is not None
    assert result["success"] is False


def test_empty_promotion_code():
    client = ShopifyCartClient()

    created_cart = client.create_cart()
    cart_id = created_cart["id"]

    result = apply_promotion.invoke(
        {
            "cart_id": cart_id,
            "discount_code": "",
        }
    )

    print("\n========== EMPTY PROMOTION ==========")
    print(result)

    assert result["success"] is False
    assert result["status"] == "invalid_request"