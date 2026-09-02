from fastapi import APIRouter

from app.api.schemas.product_schemas import (
    ProductSearchRequest,
    ProductSearchResponse,
)

from app.services.product_service import ProductService


router = APIRouter()


@router.post(
    "/search",
    response_model=ProductSearchResponse,
)
def search_products(request: ProductSearchRequest):

    return ProductService.search_products(
        query=request.query,
        max_price=request.max_price,
    )