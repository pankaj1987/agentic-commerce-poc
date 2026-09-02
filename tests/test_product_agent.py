from app.agents.product_agent import product_agent


def test_product_agent():
    result = product_agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "Why didn't I get the 20% promotion?"
                }
            ]
        }
    )

    print("\nAgent Result:")
    print(result)

   