from app.tools.product_tools import check_inventory, search_products


def test_search_products():
    # Test with a query and no max price
    result = search_products.invoke(
        {"query": "Nike running shoes", "max_price": 8000}
    )
    print(result)

    result = search_products.invoke({"query": "Nike", "max_price": 8000})

    for product in result:
        print(product["title"], product["vendor"], product["priceRangeV2"])

    print("Result without max price:")
    print(result)


def test_check_inventory():
    result = check_inventory.invoke(
        {"product_name": "Athletic Running Shoes",
        "variant_title": "US 8 / White"}
    )
    print("Inventory Result:")
    print(result)

    result1 = check_inventory.invoke(
            {"product_name": "Athletic Running Shoes",
            "variant_title": "White"}
        )
    print("Inventory Result:")
    print(result1)
        
        
     