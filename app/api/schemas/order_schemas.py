from pydantic import BaseModel, Field


class OrderHistoryRequest(BaseModel):
    customer_email: str
    limit: int = Field(default=10, ge=1, le=20)
