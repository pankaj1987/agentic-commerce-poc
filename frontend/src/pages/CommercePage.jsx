import {
  useState,
} from "react";

import ProductPage from "./ProductPage";
import Cart from "../components/Cart";
import ChatWindow from "../components/ChatWindow";

import {
  addCartItem,
  applyPromotion,
  getCart,
  removeCartItem,
  updateCartItem,
} from "../api/cartApi";

import {
  getCommerceSessionId,
} from "../utils/sessionStorage";


function CommercePage() {
  const [cart, setCart] =
    useState(null);

  const [cartLoading, setCartLoading] =
    useState(false);

  const [cartMessage, setCartMessage] =
    useState("");


  // ============================================================
  // SESSION RULE
  // ============================================================
  //
  // The browser stores only:
  //
  // agentic_commerce_session_id
  //
  // Shopify cart_id remains server-side.
  //
  // A cart is created lazily only when an ADD operation requires it.
  // ============================================================

  const requireSessionId = () => {
    const sessionId =
      getCommerceSessionId();

    if (!sessionId) {
      setCartMessage(
        "Start a conversation first so a commerce session can be created."
      );
    }

    return sessionId;
  };


  // ============================================================
  // ADD TO CART
  // ============================================================
  //
  // Backend should lazily create a Shopify cart here if:
  //
  // CommerceSession.cart_id == NULL
  //
  // ============================================================

  const handleAddToCart = async (
    variantId,
    quantity
  ) => {
    const sessionId =
      requireSessionId();

    if (!sessionId) {
      return;
    }

    setCartLoading(true);
    setCartMessage("");

    try {
      const result =
        await addCartItem(
          sessionId,
          variantId,
          quantity
        );

      if (result.success) {
        setCart(
          result.cart || null
        );

        setCartMessage(
          "Product added to cart."
        );
      } else {
        setCartMessage(
          result.message ||
            "Unable to add product to cart."
        );
      }

    } catch (error) {
      console.error(
        "Add to cart failed:",
        error
      );

      setCartMessage(
        error.response?.data?.detail ||
          "Unable to add product to cart."
      );

    } finally {
      setCartLoading(false);
    }
  };


  // ============================================================
  // UPDATE QUANTITY
  // ============================================================

  const handleUpdateQuantity = async (
    lineId,
    quantity
  ) => {
    const sessionId =
      requireSessionId();

    if (!sessionId) {
      return;
    }

    setCartLoading(true);
    setCartMessage("");

    try {
      const result =
        await updateCartItem(
          sessionId,
          lineId,
          quantity
        );

      if (result.success) {
        setCart(
          result.cart || null
        );

        setCartMessage(
          "Cart updated."
        );
      } else {
        setCartMessage(
          result.message ||
            "Unable to update cart."
        );
      }

    } catch (error) {
      console.error(
        "Quantity update failed:",
        error
      );

      setCartMessage(
        error.response?.data?.detail ||
          "Unable to update cart quantity."
      );

    } finally {
      setCartLoading(false);
    }
  };


  // ============================================================
  // REMOVE ITEM
  // ============================================================

  const handleRemove = async (
    lineId
  ) => {
    const sessionId =
      requireSessionId();

    if (!sessionId) {
      return;
    }

    setCartLoading(true);
    setCartMessage("");

    try {
      const result =
        await removeCartItem(
          sessionId,
          lineId
        );

      if (result.success) {
        setCart(
          result.cart || null
        );

        setCartMessage(
          "Product removed from cart."
        );
      } else {
        setCartMessage(
          result.message ||
            "Unable to remove product from cart."
        );
      }

    } catch (error) {
      console.error(
        "Remove item failed:",
        error
      );

      setCartMessage(
        error.response?.data?.detail ||
          "Unable to remove product from cart."
      );

    } finally {
      setCartLoading(false);
    }
  };


  // ============================================================
  // APPLY PROMOTION
  // ============================================================

  const handleApplyPromotion = async (
    discountCode
  ) => {
    const sessionId =
      requireSessionId();

    if (!sessionId) {
      return;
    }

    setCartLoading(true);
    setCartMessage("");

    try {
      const result =
        await applyPromotion(
          sessionId,
          discountCode
        );

      if (result.cart) {
        setCart(
          result.cart
        );
      }

      setCartMessage(
        result.message ||
          (
            result.success
              ? "Promotion applied."
              : "Promotion could not be applied."
          )
      );

    } catch (error) {
      console.error(
        "Promotion failed:",
        error
      );

      setCartMessage(
        error.response?.data?.detail ||
          "Unable to apply promotion."
      );

    } finally {
      setCartLoading(false);
    }
  };


  // ============================================================
  // REFRESH CART
  // ============================================================
  //
  // Called after an AI cart mutation.
  //
  // Important:
  // GET CART should NOT create a Shopify cart when cart_id is NULL.
  //
  // ============================================================

  const refreshCart = async () => {
    const sessionId =
      getCommerceSessionId();

    if (!sessionId) {
      setCart(null);
      return;
    }

    try {
      const result =
        await getCart(
          sessionId
        );

      if (result.success) {
        setCart(
          result.cart || null
        );
      }

    } catch (error) {
      console.error(
        "Unable to refresh cart:",
        error
      );
    }
  };


  // ============================================================
  // NEW CONVERSATION
  // ============================================================
  //
  // ChatWindow owns clearing the current session_id.
  //
  // We only reset the cart UI here.
  //
  // IMPORTANT:
  // Do NOT create a cart here.
  //
  // Next chat message creates the new session/thread.
  // First add-to-cart creates the Shopify cart lazily.
  // ============================================================

  const handleNewConversation = async () => {
    setCart(null);
    setCartMessage("");

    return null;
  };


  // ============================================================
  // UI
  // ============================================================

  return (
    <div>

      <header className="app-header">

        <div>
          <h1>
            Agentic Commerce
          </h1>

          <p>
            AI-powered shopping experience
          </p>
        </div>

        <div className="cart-summary">
          Cart:{" "}
          {cart?.totalQuantity || 0} items
        </div>

      </header>


      {cartMessage && (
        <div className="status-message">
          {cartMessage}
        </div>
      )}


      {cartLoading && (
        <div className="loading-message">
          Updating cart...
        </div>
      )}


      <main className="commerce-layout">

        <section className="catalog-section">

          <ProductPage
            onAddToCart={
              handleAddToCart
            }
          />

        </section>


        <aside className="cart-section">

          <Cart
            cart={cart}

            onUpdateQuantity={
              handleUpdateQuantity
            }

            onRemove={
              handleRemove
            }

            onApplyPromotion={
              handleApplyPromotion
            }
          />

        </aside>


        <section className="chat-section">

          <ChatWindow
            onCartChanged={
              refreshCart
            }

            onNewConversation={
              handleNewConversation
            }
          />

        </section>

      </main>

    </div>
  );
}


export default CommercePage;