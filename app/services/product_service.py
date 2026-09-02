from app.tools.product_tools import search_products
from app.agents.product_agent import product_agent


class ProductService:

    @staticmethod
    def search_products(
        query: str,
        max_price: float | None = None,
    ) -> dict:

        result = search_products.invoke(
            {
                "query": query,
                "max_price": max_price,
            }
        )

        if isinstance(result, str):
            return {
                "success": True,
                "products": [],
                "count": 0,
                "message": result,
            }

        return {
            "success": True,
            "products": result,
            "count": len(result),
        }

    @staticmethod
    def ask_product_agent(message: str) -> dict:

        result = product_agent.invoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": message,
                    }
                ]
            }
        )

        final_message = result["messages"][-1]

        return {
            "success": True,
            "response": final_message.content,
        }