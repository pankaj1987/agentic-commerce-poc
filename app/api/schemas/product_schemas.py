from pydantic import BaseModel, Field


class ProductSearchRequest(BaseModel):
    query: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Product search query",
    )

    max_price: float | None = Field(
        default=None,
        gt=0,
        description="Maximum price in catalog currency",
    )


class ProductSearchResponse(BaseModel):
    success: bool
    products: list[dict]
    count: int