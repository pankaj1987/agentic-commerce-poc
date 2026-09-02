from app.tools.cart_tools import (
    create_cart,
    add_to_cart,
    get_cart,
    remove_from_cart,
    update_quantity,
)

from app.clients.shopify_cart_client import ShopifyCartClient


def test_create_cart():
    client = ShopifyCartClient()

    result = client.create_cart()

    print("\nCreated Cart:")
    print(result)

    assert result is not None
    assert "id" in result
    assert result["id"]


def test_get_cart():
    client = ShopifyCartClient()

    created_cart = client.create_cart()
    cart_id = created_cart["id"]

    result = client.get_cart(cart_id)

    print("\nRetrieved Cart:")
    print(result)

    assert result is not None
    assert result["id"] == cart_id


def test_get_cart_tool():
    client = ShopifyCartClient()

    created_cart = client.create_cart()
    cart_id = created_cart["id"]

    result = get_cart.invoke(
        {
            "cart_id": cart_id
        }
    )

    print("\nCart Tool Result:")
    print(result)

    assert result["found"] is True
    assert result["cart"]["id"] == cart_id


def test_get_cart_not_found():
    client = ShopifyCartClient()

    result = client.get_cart(
        "gid://shopify/Cart/invalid-cart-id"
    )

    print("\nInvalid Cart Result:")
    print(result)

    assert result is None

def test_remove_from_cart():

    client = ShopifyCartClient()

    # 1. Create cart
    created_cart = client.create_cart()
    cart_id = created_cart["id"]

    print("\n========== CREATED CART ==========")
    print(created_cart)

    # 2. Use your known Athletic Running Shoes variant
    variant_id = "gid://shopify/ProductVariant/47993659687162"

    # 3. Add product
    added_cart = client.add_to_cart(
        cart_id=cart_id,
        variant_id=variant_id,
        quantity=1,
    )

    print("\n========== AFTER ADD ==========")
    print(added_cart)

    # 4. Get cart line ID
    lines = added_cart["lines"]["nodes"]

    assert len(lines) > 0

    line = lines[0]
    line_id = line["id"]

    print("\nCart line ID:")
    print(line_id)

    # 5. Remove product
    result = remove_from_cart.invoke(
        {
            "cart_id": cart_id,
            "line_id": line_id,
        }
    )

    print("\n========== AFTER REMOVE ==========")
    print(result)

    assert result["success"] is True

    # 6. Verify cart
    final_cart = client.get_cart(cart_id)

    assert final_cart is not None
    assert final_cart["totalQuantity"] == 0

def test_update_quantity():

    client = ShopifyCartClient()

    # 1. Create cart
    created_cart = client.create_cart()
    cart_id = created_cart["id"]

    # 2. Add Athletic Running Shoes
    variant_id = "gid://shopify/ProductVariant/47993659687162"

    added_cart = client.add_to_cart(
        cart_id=cart_id,
        variant_id=variant_id,
        quantity=1,
    )

    print("\n========== AFTER ADD ==========")
    print(added_cart)

    # 3. Get cart line
    lines = added_cart["lines"]["nodes"]

    assert len(lines) > 0

    line_id = lines[0]["id"]

    print("\nCart line ID:")
    print(line_id)

    # 4. Update quantity to 3
    result = update_quantity.invoke(
        {
            "cart_id": cart_id,
            "line_id": line_id,
            "quantity": 3,
        }
    )

    print("\n========== AFTER UPDATE ==========")
    print(result)

    assert result["success"] is True

    # 5. Verify Shopify cart
    final_cart = client.get_cart(cart_id)

    assert final_cart is not None
    assert final_cart["totalQuantity"] == 3

    final_line = final_cart["lines"]["nodes"][0]

    assert final_line["quantity"] == 3