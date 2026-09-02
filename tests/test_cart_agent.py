from app.agents.cart_agent import cart_agent
from app.clients.shopify_cart_client import ShopifyCartClient
from app.clients.shopify_client import ShopifyClient


def print_agent_result(result: dict) -> None:
    print("\n========== CART AGENT ==========")
    for message in result["messages"]:
        print("\nMessage:")
        print(message)


def test_cart_agent_get_cart():
    client = ShopifyCartClient()

    created_cart = client.create_cart()
    cart_id = created_cart["id"]

    result = cart_agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "Please show me the contents of my cart. "
                        f"The cart ID is {cart_id}."
                    ),
                }
            ]
        }
    )

    print_agent_result(result)

    final_message = result["messages"][-1]
    assert final_message.content


def test_cart_agent_add_product():
    client = ShopifyCartClient()

    # Create cart
    created_cart = client.create_cart()
    cart_id = created_cart["id"]

    # Ask agent to add product
    result = cart_agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "Add Athletic Running Shoes to my cart. "
                        f"My cart ID is {cart_id}."
                    ),
                }
            ]
        }
    )

    print_agent_result(result)

    # Verify actual Shopify cart
    cart = client.get_cart(cart_id)

    assert cart is not None
    assert cart["totalQuantity"] >= 1
    assert len(cart["lines"]["nodes"]) >= 1

    print("\n========== FINAL SHOPIFY CART ==========")
    print(cart)


def test_cart_agent_add_product_customer_request():
    client = ShopifyCartClient()

    created_cart = client.create_cart()
    cart_id = created_cart["id"]

    result = cart_agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": (
                        f"My cart ID is {cart_id}. "
                        "Please add Athletic Running Shoes to my cart."
                    ),
                }
            ]
        }
    )

    print("\n========== CUSTOMER REQUEST ==========")
    for message in result["messages"]:
        print(message)

    final_message = result["messages"][-1]
    assert final_message.content


def test_cart_agent_remove_product():
    client = ShopifyCartClient()

    # Create cart
    created_cart = client.create_cart()
    cart_id = created_cart["id"]

    # Resolve the product variant
    product_client = ShopifyClient()
    variant = product_client.find_product_variant(
        product_query="Athletic Running Shoes"
    )

    assert variant is not None

    # Add product directly so the test has a cart line
    client.add_to_cart(
        cart_id=cart_id,
        variant_id=variant["variant_id"],
        quantity=1,
    )

    # Get actual cart line
    cart = client.get_cart(cart_id)

    assert cart is not None
    assert len(cart["lines"]["nodes"]) > 0

    result = cart_agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "Remove Athletic Running Shoes from my cart. "
                        f"My cart ID is {cart_id}."
                    ),
                }
            ]
        }
    )

    print_agent_result(result)

    final_message = result["messages"][-1]
    assert final_message.content

    # Verify actual Shopify cart
    updated_cart = client.get_cart(cart_id)
    assert updated_cart is not None


def test_cart_agent_update_quantity():
    client = ShopifyCartClient()

    # Create cart
    created_cart = client.create_cart()
    cart_id = created_cart["id"]

    # Resolve product
    product_client = ShopifyClient()
    variant = product_client.find_product_variant(
        product_query="Athletic Running Shoes"
    )

    assert variant is not None

    # Add one item
    client.add_to_cart(
        cart_id=cart_id,
        variant_id=variant["variant_id"],
        quantity=1,
    )

    result = cart_agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "Change the quantity of Athletic Running Shoes "
                        f"to 2. My cart ID is {cart_id}."
                    ),
                }
            ]
        }
    )

    print_agent_result(result)

    final_message = result["messages"][-1]
    assert final_message.content

    # Verify Shopify
    updated_cart = client.get_cart(cart_id)
    assert updated_cart is not None

    lines = updated_cart["lines"]["nodes"]
    assert len(lines) > 0
    assert lines[0]["quantity"] == 2


def test_cart_agent_add_product_customer_friendly():
    client = ShopifyCartClient()

    created_cart = client.create_cart()
    cart_id = created_cart["id"]

    result = cart_agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "Please add Athletic Running Shoes to my cart. "
                        f"The cart ID is {cart_id}."
                    ),
                }
            ]
        }
    )

    print_agent_result(result)

    final_message = result["messages"][-1]
    assert final_message.content