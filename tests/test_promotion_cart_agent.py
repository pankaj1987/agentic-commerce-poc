
from app.agents.cart_agent import cart_agent
from app.clients.shopify_cart_client import ShopifyCartClient

def test_cart_agent_apply_promotion():
    client = ShopifyCartClient()

    # Create cart
    created_cart = client.create_cart()
    cart_id = created_cart["id"]

    # Add product first
    variant_id = "gid://shopify/ProductVariant/47993659654394"

    client.add_to_cart(
        cart_id=cart_id,
        variant_id=variant_id,
        quantity=1,
    )

    # Ask agent to apply promotion
    result = cart_agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": (
                        f"My cart ID is {cart_id}. "
                        "Please apply promotion code SAVE20 "
                        "to my cart."
                    ),
                }
            ]
        }
    )

    print("\n========== CART AGENT PROMOTION ==========")

    for message in result["messages"]:
        print("\nMessage:")
        print(message)

    final_message = result["messages"][-1]

    assert final_message.content


def test_cart_agent_apply_promotion_customer_request():
    client = ShopifyCartClient()

    created_cart = client.create_cart()
    cart_id = created_cart["id"]

    variant_id = "gid://shopify/ProductVariant/47993659654394"

    client.add_to_cart(
        cart_id=cart_id,
        variant_id=variant_id,
        quantity=4,
    )

    result = cart_agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "I have a cart. "
                        f"The cart ID is {cart_id}. "
                        "Can you apply 6ARH7B1F6YN9?"
                    ),
                }
            ]
        }
    )

    print("\n========== CUSTOMER PROMOTION REQUEST ==========")

    for message in result["messages"]:
        print(message)

    final_message = result["messages"][-1]

    assert final_message.content


def test_cart_agent_promotion_explanation():
    client = ShopifyCartClient()

    created_cart = client.create_cart()
    cart_id = created_cart["id"]

    variant_id = "gid://shopify/ProductVariant/47993659654394"

    client.add_to_cart(
        cart_id=cart_id,
        variant_id=variant_id,
        quantity=1,
    )

    result = cart_agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": (
                        f"My cart ID is {cart_id}. "
                        "Why wasn't my 20% promotion applied?"
                    ),
                }
            ]
        }
    )

    print("\n========== PROMOTION EXPLANATION ==========")

    for message in result["messages"]:
        print("\nMessage:")
        print(message)

    final_message = result["messages"][-1]

    assert final_message.content