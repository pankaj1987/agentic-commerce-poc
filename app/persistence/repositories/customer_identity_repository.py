from __future__ import annotations

from sqlalchemy import select

from app.persistence.database import SessionLocal
from app.persistence.models import CustomerIdentity


class CustomerIdentityRepository:
    @staticmethod
    def get_by_user_id(user_id: str) -> CustomerIdentity | None:
        with SessionLocal() as db:
            return db.scalar(select(CustomerIdentity).where(CustomerIdentity.user_id == user_id))

    @staticmethod
    def get_by_shopify_customer_id(shopify_customer_id: str) -> CustomerIdentity | None:
        with SessionLocal() as db:
            return db.scalar(
                select(CustomerIdentity).where(
                    CustomerIdentity.shopify_customer_id == shopify_customer_id
                )
            )

    @staticmethod
    def upsert_mapping(user_id: str, shopify_customer_id: str) -> CustomerIdentity:
        user_id = (user_id or "").strip()
        shopify_customer_id = (shopify_customer_id or "").strip()
        if not user_id or not shopify_customer_id:
            raise ValueError("Both user_id and shopify_customer_id are required.")

        with SessionLocal() as db:
            existing_customer = db.scalar(
                select(CustomerIdentity).where(
                    CustomerIdentity.shopify_customer_id == shopify_customer_id,
                    CustomerIdentity.user_id != user_id,
                )
            )
            if existing_customer:
                raise PermissionError("This Shopify customer is already mapped to another application user.")

            mapping = db.get(CustomerIdentity, user_id)
            if mapping is None:
                mapping = CustomerIdentity(user_id=user_id, shopify_customer_id=shopify_customer_id)
                db.add(mapping)
            else:
                mapping.shopify_customer_id = shopify_customer_id
                mapping.status = "ACTIVE"

            db.commit()
            db.refresh(mapping)
            return mapping
