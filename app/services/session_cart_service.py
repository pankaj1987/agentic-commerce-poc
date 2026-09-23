"""Session-aware cart application service.

The browser owns only session_id. The Shopify cart ID is resolved from the
persisted CommerceSession and never needs to be sent back by the client.
"""

from app.persistence.models import CommerceSession
from app.persistence.repositories.session_repository import SessionRepository
from app.services.cart_service import CartService
from app.services.session_service import SessionService


class SessionCartService:
    @staticmethod
    def _resolve_session(
        session_id: str | None,
        user_id: str,
    ) -> CommerceSession:
        return SessionService.get_or_create_session(session_id, user_id=user_id)

    @staticmethod
    def _public_result(
        commerce_session: CommerceSession,
        result: dict,
    ) -> dict:
        # Never expose the opaque Shopify cart ID to the browser.
        # Cart line IDs are still returned because the UI needs them for
        # update/remove operations.
        public_result = dict(result)

        cart = public_result.get("cart")
        if isinstance(cart, dict):
            public_cart = dict(cart)
            public_cart.pop("id", None)
            public_result["cart"] = public_cart

        public_result["session_id"] = commerce_session.session_id
        return public_result

    @staticmethod
    def _create_and_associate_cart(
        commerce_session: CommerceSession,
    ) -> tuple[CommerceSession, dict]:
        result = CartService.create_cart()
        if not result.get("success") or not result.get("cart"):
            return commerce_session, result

        cart_id = result["cart"].get("id")
        if not cart_id:
            return commerce_session, {
                "success": False,
                "message": "Shopify returned a cart without an ID.",
            }

        commerce_session = SessionRepository.update_cart_id(
            commerce_session.session_id,
            cart_id,
        )
        return commerce_session, result

    @staticmethod
    def initialize_cart(
        session_id: str | None,
        user_id: str,
    ) -> dict:
        """Create/reuse the cart for one public commerce session."""

        commerce_session = SessionCartService._resolve_session(session_id, user_id)

        if commerce_session.cart_id:
            existing = CartService.get_cart(commerce_session.cart_id)
            if existing.get("success") and existing.get("cart"):
                SessionRepository.touch_session(commerce_session.session_id)
                return SessionCartService._public_result(
                    commerce_session,
                    existing,
                )

        commerce_session, result = (
            SessionCartService._create_and_associate_cart(commerce_session)
        )
        return SessionCartService._public_result(commerce_session, result)

    @staticmethod
    def get_cart(
        session_id: str,
        user_id: str,
    ) -> dict:
        commerce_session = SessionCartService._resolve_session(session_id, user_id)

        if not commerce_session.cart_id:
            return {
                "success": True,
                "session_id": commerce_session.session_id,
                "cart": None,
                "message": "No active shopping cart was found.",
            }

        result = CartService.get_cart(commerce_session.cart_id)
        SessionRepository.touch_session(commerce_session.session_id)
        return SessionCartService._public_result(commerce_session, result)

    @staticmethod
    def add_item(
        session_id: str,
        variant_id: str,
        quantity: int,
        user_id: str,
    ) -> dict:
        commerce_session = SessionCartService._resolve_session(session_id, user_id)

        if not commerce_session.cart_id:
            commerce_session, create_result = (
                SessionCartService._create_and_associate_cart(commerce_session)
            )
            if not create_result.get("success"):
                return SessionCartService._public_result(
                    commerce_session,
                    create_result,
                )

        result = CartService.add_to_cart(
            cart_id=commerce_session.cart_id,
            variant_id=variant_id,
            quantity=quantity,
        )
        SessionRepository.touch_session(commerce_session.session_id)
        return SessionCartService._public_result(commerce_session, result)

    @staticmethod
    def update_item(
        session_id: str,
        line_id: str,
        quantity: int,
        user_id: str,
    ) -> dict:
        commerce_session = SessionCartService._resolve_session(session_id, user_id)
        if not commerce_session.cart_id:
            return {
                "success": False,
                "session_id": commerce_session.session_id,
                "message": "No active shopping cart was found.",
            }

        result = CartService.update_item(
            cart_id=commerce_session.cart_id,
            line_id=line_id,
            quantity=quantity,
        )
        SessionRepository.touch_session(commerce_session.session_id)
        return SessionCartService._public_result(commerce_session, result)

    @staticmethod
    def remove_item(
        session_id: str,
        line_id: str,
        user_id: str,
    ) -> dict:
        commerce_session = SessionCartService._resolve_session(session_id, user_id)
        if not commerce_session.cart_id:
            return {
                "success": False,
                "session_id": commerce_session.session_id,
                "message": "No active shopping cart was found.",
            }

        result = CartService.remove_item(
            cart_id=commerce_session.cart_id,
            line_id=line_id,
        )
        SessionRepository.touch_session(commerce_session.session_id)
        return SessionCartService._public_result(commerce_session, result)

    @staticmethod
    def apply_discount(
        session_id: str,
        discount_code: str,
        user_id: str,
    ) -> dict:
        commerce_session = SessionCartService._resolve_session(session_id, user_id)
        if not commerce_session.cart_id:
            return {
                "success": False,
                "session_id": commerce_session.session_id,
                "message": "No active shopping cart was found.",
            }

        result = CartService.apply_discount(
            cart_id=commerce_session.cart_id,
            discount_code=discount_code,
        )
        SessionRepository.touch_session(commerce_session.session_id)
        return SessionCartService._public_result(commerce_session, result)
