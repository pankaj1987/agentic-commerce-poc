from openai import AzureOpenAI

from app.config.settings import settings


client = AzureOpenAI(
    api_key=settings.azure_openai_api_key,
    api_version=settings.azure_openai_api_version,
    azure_endpoint=settings.azure_openai_endpoint,
)

response = client.chat.completions.create(
    model=settings.azure_openai_deployment,
    messages=[
        {
            "role": "user",
            "content": "Explain Google UCP in two sentences."
        }
    ],
)

print(response.choices[0].message.content)