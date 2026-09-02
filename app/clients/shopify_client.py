import httpx

from app.config.settings import settings


class ShopifyClient:

    def __init__(self):
        self.url = (
            f"https://{settings.shopify_store_domain}"
            f"/admin/api/{settings.shopify_api_version}/graphql.json"
        )
        self.headers = {
            "Content-Type": "application/json",
            "X-Shopify-Access-Token": settings.shopify_access_token,
        }

    def execute_query(
        self, query: str, variables: dict | None = None
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

    def search_products(self, query: str, first: int = 10) -> list[dict]:
        graphql_query = """
        query SearchProducts($query: String, $first: Int!) {
            products(
                first: $first,
                query: $query
            ) {
                nodes {
                    id
                    title
                    handle
                    description
                    vendor
                    productType
                    totalInventory
                    priceRangeV2 {
                        minVariantPrice {
                            amount
                            currencyCode
                        }
                        maxVariantPrice {
                            amount
                            currencyCode
                        }
                    }
                }
            }
        }
        """

        data = self.execute_query(
            graphql_query,
            {
                "query": query,
                "first": first,
            },
        )
        products = data["products"]["nodes"]
        results = []
        for product in products:
            min_price = product["priceRangeV2"]["minVariantPrice"]
            max_price = product["priceRangeV2"]["maxVariantPrice"]
            results.append(
                {
                    "id": product["id"],
                    "title": product["title"],
                    "handle": product["handle"],
                    "description": product["description"],
                    "brand": product["vendor"],
                    "product_type": product["productType"],
                    "inventory": product["totalInventory"],
                    "price": {
                        "min_amount": float(min_price["amount"]),
                        "max_amount": float(max_price["amount"]),
                        "currency": min_price["currencyCode"],
                    },
                }
            )
        return results

    def get_product(self, product_id: str) -> dict | None:
        graphql_query = """
        query GetProduct($id: ID!) {
            product(id: $id) {
                id
                title
                handle
                description
                vendor
                productType
                totalInventory

                priceRangeV2 {
                    minVariantPrice {
                        amount
                        currencyCode
                    }
                    maxVariantPrice {
                        amount
                        currencyCode
                    }
                }

                variants(first: 10) {
                    nodes {
                        id
                        title
                        sku
                        price
                        inventoryQuantity
                    }
                }
            }
        }
        """

        data = self.execute_query(
            graphql_query,
            {
                "id": product_id,
            },
        )
        return data["product"]

    # Find variant
    def find_product_variant(
        self, product_query: str, variant_title: str | None = None
    ) -> dict | None:
        graphql_query = """
        query FindProductVariant($query: String!) {
            products(first: 10, query: $query) {
                nodes {
                    id
                    title

                    variants(first: 50) {
                        nodes {
                            id
                            title
                            sku
                        }
                    }
                }
            }
        }
        """

        data = self.execute_query(
            graphql_query,
            {
                "query": product_query,
            },
        )

        products = data["products"]["nodes"]

        # -------------------------------------------------
        # 0 products -> Product not found
        # -------------------------------------------------
        if not products:
            return {
                "found": False,
                "multiple_matches": False,
                "message": f"No product found for '{product_query}'",
            }

        # -------------------------------------------------
        # >1 products -> Return candidates
        # -------------------------------------------------
        if len(products) > 1:
            return {
                "found": True,
                "multiple_matches": True,
                "candidates": [
                    {
                        "product_id": product["id"],
                        "product_title": product["title"],
                    }
                    for product in products
                ],
            }

        # -------------------------------------------------
        # Exactly 1 product -> Continue
        # -------------------------------------------------
        product = products[0]
        variants = product["variants"]["nodes"]

        # -------------------------------------------------
        # Variant specified -> find matching variant
        # -------------------------------------------------
        if variant_title:
            search_variant = variant_title.lower().strip()

            # ---------------------------------------------
            # First try exact match
            # ---------------------------------------------
            exact_matches = [
                variant
                for variant in variants
                if variant["title"].lower().strip() == search_variant
            ]

            if len(exact_matches) == 1:
                variant = exact_matches[0]
                return {
                    "found": True,
                    "multiple_matches": False,
                    "product_id": product["id"],
                    "product_title": product["title"],
                    "variant_id": variant["id"],
                    "variant_title": variant["title"],
                    "sku": variant["sku"],
                }

            # ---------------------------------------------
            # Then try partial match
            # ---------------------------------------------
            partial_matches = [
                variant
                for variant in variants
                if search_variant in variant["title"].lower()
            ]

            # One partial match
            if len(partial_matches) == 1:
                variant = partial_matches[0]
                return {
                    "found": True,
                    "multiple_matches": False,
                    "product_id": product["id"],
                    "product_title": product["title"],
                    "variant_id": variant["id"],
                    "variant_title": variant["title"],
                    "sku": variant["sku"],
                }

            # Multiple partial matches
            if len(partial_matches) > 1:
                return {
                    "found": True,
                    "multiple_matches": True,
                    "product_id": product["id"],
                    "product_title": product["title"],
                    "variant_candidates": [
                        {
                            "variant_id": variant["id"],
                            "variant_title": variant["title"],
                            "sku": variant["sku"],
                        }
                        for variant in partial_matches
                    ],
                }

            # No variant found
            return {
                "found": False,
                "multiple_matches": False,
                "product_id": product["id"],
                "product_title": product["title"],
                "message": (
                    f"Variant '{variant_title}' was not found "
                    f"for product '{product['title']}'"
                ),
            }

        # -------------------------------------------------
        # No variant specified
        # -------------------------------------------------
        if variants:
            variant = variants[0]
            return {
                "found": True,
                "multiple_matches": False,
                "product_id": product["id"],
                "product_title": product["title"],
                "variant_id": variant["id"],
                "variant_title": variant["title"],
                "sku": variant["sku"],
            }

        # Product exists but has no variants
        return {
            "found": False,
            "multiple_matches": False,
            "product_id": product["id"],
            "product_title": product["title"],
            "message": f"No variants found for product '{product['title']}'",
        }

    # Check inventory for a specific product variant
    def check_inventory(
        self, variant_id: str, location_id: str | None = None
    ) -> dict:
        graphql_query = """
        query GetVariantInventory($variantId: ID!) {
            productVariant(id: $variantId) {
                id
                title
                sku
                product {
                    id
                    title
                }

                inventoryItem {
                    id
                    tracked

                    inventoryLevels(first: 20) {
                        nodes {
                            location {
                                id
                                name
                            }

                            quantities(
                                names: ["available", "on_hand", "committed", "incoming"]
                            ) {
                                name
                                quantity
                            }
                        }
                    }
                }
            }
        }
        """

        data = self.execute_query(
            graphql_query,
            {
                "variantId": variant_id,
            },
        )

        variant = data["productVariant"]
        if variant is None:
            raise ValueError(f"Product variant not found: {variant_id}")

        inventory_item = variant["inventoryItem"]
        if inventory_item is None:
            return {
                "variant_id": variant_id,
                "tracked": False,
                "locations": [],
            }

        locations = []
        for level in inventory_item["inventoryLevels"]["nodes"]:
            location = level["location"]

            quantities = {
                quantity["name"]: quantity["quantity"]
                for quantity in level["quantities"]
            }

            if location_id is not None and location["id"] != location_id:
                continue

            locations.append(
                {
                    "location_id": location["id"],
                    "location_name": location["name"],
                    "available": quantities.get("available", 0),
                    "on_hand": quantities.get("on_hand", 0),
                    "committed": quantities.get("committed", 0),
                    "incoming": quantities.get("incoming", 0),
                }
            )

        return {
            "product_id": variant["product"]["id"],
            "product_title": variant["product"]["title"],
            "variant_id": variant["id"],
            "variant_title": variant["title"],
            "sku": variant["sku"],
            "inventory_item_id": inventory_item["id"],
            "tracked": inventory_item["tracked"],
            "locations": locations,
        }