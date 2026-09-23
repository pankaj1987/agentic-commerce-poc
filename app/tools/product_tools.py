from langchain.tools import tool

from app.clients.shopify_client import ShopifyClient
from app.security.tool_authorization import authorize_current_tool


@tool
def search_products(
    query: str,
    max_price: float | None = None,
):
    """Search products in the commerce catalog.

    Args:
        query:
            Customer's product search query.

        max_price:
            Optional maximum price requested by the customer.

    Returns:
        Matching products with product details and pricing.
    """

    authorize_current_tool("search_products")
    shopify_client = ShopifyClient()

    products = shopify_client.search_products(
        query=query,
        first=10,
    )

    if max_price is not None:
        filtered_products = []

        for product in products:
            price = product["price"]

            if price["min_amount"] <= max_price:
                filtered_products.append(product)

        products = filtered_products

    return products


@tool
def get_product(product_id: str):
    """Retrieve detailed information about a Shopify product.

    Args:
        product_id: Shopify product GraphQL ID.

    Returns:
        Product details including variants, pricing and inventory.
    """
    authorize_current_tool("search_products")
    shopify_client = ShopifyClient()
    return shopify_client.get_product(product_id)


@tool
def check_inventory(
    product_name: str,
    variant_title: str | None = None,
    location_id: str | None = None,
):
    """Check inventory for a product.
    Use this tool when the customer asks whether a product
    or product variant is currently in stock.

    Args:
        product_name:
            Customer-facing product name, for example
            'Athletic Running Shoes'.

        variant_title:
            Optional variant such as 'US 8 / White'.

        location_id:
            Optional Shopify location ID.

    Returns:
        Current inventory information.
    """
    authorize_current_tool("check_inventory")
    shopify_client = ShopifyClient()

    variant = shopify_client.find_product_variant(
        product_query=product_name,
        variant_title=variant_title,
    )

    # Product/variant not found
    if not variant.get("found", False):
        return variant

    # Multiple products found
    if variant.get("multiple_matches", False):
        return variant

    # At this point we should have a variant_id
    inventory = shopify_client.check_inventory(
        variant_id=variant["variant_id"],
        location_id=location_id,
    )

    return {
        "found": True,
        "product": variant,
        "inventory": inventory,
    }

@tool
def find_product_variant(
    product_name: str,
    variant_title: str | None = None,
) -> dict:
    """Find a product variant from the Shopify catalog.

    Use this to resolve a customer-facing product name and
    optional variant information into a Shopify variant ID.

    Args:
        product_name:
            Customer-facing product name.

        variant_title:
            Optional variant such as 'US 8 / White'.

    Returns:
        Matching product/variant information.
    """

    authorize_current_tool("search_products")
    shopify_client = ShopifyClient()

    result = shopify_client.find_product_variant(
        product_query=product_name,
        variant_title=variant_title,
    )

    if result is None:
        return {
            "found": False,
            "message": f"No product found for '{product_name}'",
        }

    return result