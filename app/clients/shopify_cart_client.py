import httpx

from app.config.settings import settings


class ShopifyCartClient:

    def __init__(self):
        self.url = (
            f"https://{settings.shopify_store_domain}"
            f"/api/{settings.shopify_api_version}/graphql.json"
        )
        self.headers = {
            "Content-Type": "application/json",
            "X-Shopify-Storefront-Access-Token": settings.shopify_storefront_token,
        }

    def execute_query(
        self,
        query: str,
        variables: dict | None = None,
    ) -> dict:
        payload = {
            "query": query,
            "variables": variables or {},
        }

        response = httpx.post(
            self.url,
            headers=self.headers,
            json=payload,
            timeout=30.0,
        )
        response.raise_for_status()
        result = response.json()

        if "errors" in result:
            raise RuntimeError(f"Shopify GraphQL error: {result['errors']}")

        return result["data"]

    def create_cart(self) -> dict:
        graphql_query = """
        mutation CreateCart {
            cartCreate {
                cart {
                    id
                    checkoutUrl
                    totalQuantity
                    cost {
                        subtotalAmount {
                            amount
                            currencyCode
                        }
                        totalAmount {
                            amount
                            currencyCode
                        }
                    }
                    lines(first: 50) {
                        nodes {
                            id
                            quantity
                            merchandise {
                                ... on ProductVariant {
                                    id
                                    title
                                    product {
                                        id
                                        title
                                    }
                                }
                            }
                            cost {
                                amountPerQuantity {
                                    amount
                                    currencyCode
                                }
                                totalAmount {
                                    amount
                                    currencyCode
                                }
                            }
                        }
                    }
                }
                userErrors {
                    field
                    message
                }
            }
        }
        """

        data = self.execute_query(graphql_query)
        result = data["cartCreate"]

        if result["userErrors"]:
            raise RuntimeError(f"Cart creation failed: {result['userErrors']}")

        return result["cart"]

    def get_cart(self, cart_id: str) -> dict | None:
        graphql_query = """
        query GetCart($cartId: ID!) {
            cart(id: $cartId) {
                id
                checkoutUrl
                totalQuantity
                discountCodes {
                    code
                    applicable
                }
                cost {
                    subtotalAmount {
                        amount
                        currencyCode
                    }
                    totalAmount {
                        amount
                        currencyCode
                    }
                }
                lines(first: 50) {
                    nodes {
                        id
                        quantity
                        merchandise {
                            ... on ProductVariant {
                                id
                                title
                                product {
                                    id
                                    title
                                }
                            }
                        }
                        cost {
                            amountPerQuantity {
                                amount
                                currencyCode
                            }
                            totalAmount {
                                amount
                                currencyCode
                            }
                        }
                    }
                }
            }
        }
        """

        data = self.execute_query(
            graphql_query,
            {"cartId": cart_id},
        )

        return data["cart"]

    def add_to_cart(
        self,
        cart_id: str,
        variant_id: str,
        quantity: int,
    ) -> dict:
        graphql_query = """
        mutation AddToCart(
            $cartId: ID!
            $lines: [CartLineInput!]!
        ) {
            cartLinesAdd(
                cartId: $cartId
                lines: $lines
            ) {
                cart {
                    id
                    checkoutUrl
                    totalQuantity
                    cost {
                        subtotalAmount {
                            amount
                            currencyCode
                        }
                        totalAmount {
                            amount
                            currencyCode
                        }
                    }
                    lines(first: 50) {
                        nodes {
                            id
                            quantity
                            merchandise {
                                ... on ProductVariant {
                                    id
                                    title
                                    product {
                                        id
                                        title
                                    }
                                }
                            }
                            cost {
                                totalAmount {
                                    amount
                                    currencyCode
                                }
                            }
                        }
                    }
                }
                userErrors {
                    field
                    message
                }
            }
        }
        """

        variables = {
            "cartId": cart_id,
            "lines": [
                {
                    "merchandiseId": variant_id,
                    "quantity": quantity,
                }
            ],
        }

        data = self.execute_query(
            graphql_query,
            variables,
        )

        result = data["cartLinesAdd"]

        if result["userErrors"]:
            raise RuntimeError(f"Unable to add product: {result['userErrors']}")

        return result["cart"]

    def remove_from_cart(
        self,
        cart_id: str,
        line_id: str,
    ) -> dict:
        graphql_query = """
        mutation RemoveFromCart(
            $cartId: ID!
            $lineIds: [ID!]!
        ) {
            cartLinesRemove(
                cartId: $cartId
                lineIds: $lineIds
            ) {
                cart {
                    id
                    checkoutUrl
                    totalQuantity
                    cost {
                        subtotalAmount {
                            amount
                            currencyCode
                        }
                        totalAmount {
                            amount
                            currencyCode
                        }
                    }
                    lines(first: 50) {
                        nodes {
                            id
                            quantity
                            merchandise {
                                ... on ProductVariant {
                                    id
                                    title
                                    product {
                                        id
                                        title
                                    }
                                }
                            }
                            cost {
                                amountPerQuantity {
                                    amount
                                    currencyCode
                                }
                                totalAmount {
                                    amount
                                    currencyCode
                                }
                            }
                        }
                    }
                }
                userErrors {
                    field
                    message
                }
            }
        }
        """

        variables = {
            "cartId": cart_id,
            "lineIds": [line_id],
        }

        data = self.execute_query(
            graphql_query,
            variables,
        )

        result = data["cartLinesRemove"]

        if result["userErrors"]:
            raise RuntimeError(
                f"Unable to remove product: {result['userErrors']}"
            )

        return result["cart"]

    def update_quantity(
        self,
        cart_id: str,
        line_id: str,
        quantity: int,
    ) -> dict:
        graphql_query = """
        mutation UpdateCartLine(
            $cartId: ID!
            $lines: [CartLineUpdateInput!]!
        ) {
            cartLinesUpdate(
                cartId: $cartId
                lines: $lines
            ) {
                cart {
                    id
                    checkoutUrl
                    totalQuantity
                    cost {
                        subtotalAmount {
                            amount
                            currencyCode
                        }
                        totalAmount {
                            amount
                            currencyCode
                        }
                    }
                    lines(first: 50) {
                        nodes {
                            id
                            quantity
                            merchandise {
                                ... on ProductVariant {
                                    id
                                    title
                                    product {
                                        id
                                        title
                                    }
                                }
                            }
                            cost {
                                amountPerQuantity {
                                    amount
                                    currencyCode
                                }
                                totalAmount {
                                    amount
                                    currencyCode
                                }
                            }
                        }
                    }
                }
                userErrors {
                    field
                    message
                }
            }
        }
        """

        variables = {
            "cartId": cart_id,
            "lines": [
                {
                    "id": line_id,
                    "quantity": quantity,
                }
            ],
        }

        data = self.execute_query(
            graphql_query,
            variables,
        )

        result = data["cartLinesUpdate"]

        if result["userErrors"]:
            raise RuntimeError(
                f"Unable to update quantity: {result['userErrors']}"
            )

        return result["cart"]

    def apply_discount_code(
        self,
        cart_id: str,
        discount_code: str,
    ) -> dict:
        graphql_query = """
        mutation CartDiscountCodesUpdate(
            $cartId: ID!
            $discountCodes: [String!]!
        ) {
            cartDiscountCodesUpdate(
                cartId: $cartId
                discountCodes: $discountCodes
            ) {
                cart {
                    id
                    checkoutUrl
                    totalQuantity
                    discountCodes {
                        code
                        applicable
                    }
                    cost {
                        subtotalAmount {
                            amount
                            currencyCode
                        }
                        totalAmount {
                            amount
                            currencyCode
                        }
                    }
                    lines(first: 50) {
                        nodes {
                            id
                            quantity
                            merchandise {
                                ... on ProductVariant {
                                    id
                                    title
                                    product {
                                        id
                                        title
                                    }
                                }
                            }
                            cost {
                                amountPerQuantity {
                                    amount
                                    currencyCode
                                }
                                totalAmount {
                                    amount
                                    currencyCode
                                }
                            }
                        }
                    }
                }
                userErrors {
                    field
                    message
                    code
                }
                warnings {
                    code
                    message
                    target
                }
            }
        }
        """

        variables = {
            "cartId": cart_id,
            "discountCodes": [discount_code.strip()],
        }

        data = self.execute_query(
            graphql_query,
            variables,
        )

        result = data["cartDiscountCodesUpdate"]

        return {
            "cart": result["cart"],
            "user_errors": result["userErrors"],
            "warnings": result["warnings"],
        }