import {
  useEffect,
  useRef,
  useState,
} from "react";

import ProductPage from "./ProductPage";

import Cart from "../components/Cart";
import ChatWindow from "../components/ChatWindow";

import {
  createCart,
  getCart,
  addCartItem,
  updateCartItem,
  removeCartItem,
  applyPromotion,
} from "../api/cartApi";


function CommercePage() {
  // ============================================================
  // CART STATE
  // ============================================================
  //
  // IMPORTANT:
  //
  // cartId is currently kept ONLY in React memory because the
  // existing direct Cart REST APIs still use Shopify cart_id.
  //
  // It must NOT be stored in localStorage.
  //
  // The chat flow does not receive this cartId.
  //
  // Once cartApi is migrated to session_id, this cartId state
  // can be removed completely.
  // ============================================================

  const [cartId, setCartId] =
    useState(null);

  const [cart, setCart] =
    useState(null);

  const [cartLoading, setCartLoading] =
    useState(false);

  const [cartMessage, setCartMessage] =
    useState("");

  // Prevent duplicate cart initialization caused by
  // React StrictMode during development.
  const cartInitializationStarted =
    useRef(false);


  // ============================================================
  // INITIALIZE UI CART
  // ============================================================
  //
  // OLD DESIGN:
  //
  // localStorage
  //     ↓
  // shopify_cart_id
  //     ↓
  // restore Shopify cart
  //
  //
  // CURRENT TRANSITIONAL DESIGN:
  //
  // Page load
  //     ↓
  // create temporary UI cart
  //     ↓
  // cartId exists only in React memory
  //
  //
  // Chat session/cart ownership is handled independently by
  // backend CommerceSession + LangGraph.
  // ============================================================

  useEffect(() => {
    if (
      cartInitializationStarted.current
    ) {
      return;
    }

    cartInitializationStarted.current =
      true;

    initializeCart();
  }, []);


  // ============================================================
  // CREATE NEW UI CART
  // ============================================================

  const initializeCart =
    async () => {
      setCartLoading(
        true
      );

      setCartMessage(
        ""
      );

      try {
        const result =
          await createCart();

        if (
          result.success &&
          result.cart
        ) {
          setCart(
            result.cart
          );

          setCartId(
            result.cart.id
          );

          // ====================================================
          // IMPORTANT
          // ====================================================
          //
          // DO NOT persist:
          //
          // localStorage.setItem(
          //   "shopify_cart_id",
          //   result.cart.id
          // );
          //
          // Shopify cart IDs must not be persisted in browser
          // storage in the Phase 3 architecture.
          // ====================================================

          console.log(
            "UI cart created successfully."
          );

        } else {
          setCartMessage(
            result.message ||
              "Unable to create shopping cart."
          );
        }

      } catch (error) {
        console.error(
          "Unable to create cart:",
          error
        );

        setCartMessage(
          error.response?.data?.detail ||
            "Unable to create shopping cart."
        );

      } finally {
        setCartLoading(
          false
        );
      }
    };


  // ============================================================
  // ADD TO CART
  // ============================================================

  const handleAddToCart =
    async (
      variantId,
      quantity
    ) => {
      if (!cartId) {
        setCartMessage(
          "Shopping cart is not ready yet."
        );

        return;
      }

      setCartLoading(
        true
      );

      setCartMessage(
        ""
      );

      try {
        const result =
          await addCartItem(
            cartId,
            variantId,
            quantity
          );

        if (result.success) {
          setCart(
            result.cart
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
        setCartLoading(
          false
        );
      }
    };


  // ============================================================
  // UPDATE QUANTITY
  // ============================================================

  const handleUpdateQuantity =
    async (
      lineId,
      quantity
    ) => {
      if (!cartId) {
        return;
      }

      setCartLoading(
        true
      );

      setCartMessage(
        ""
      );

      try {
        const result =
          await updateCartItem(
            cartId,
            lineId,
            quantity
          );

        if (result.success) {
          setCart(
            result.cart
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
        setCartLoading(
          false
        );
      }
    };


  // ============================================================
  // REMOVE ITEM
  // ============================================================

  const handleRemove =
    async (
      lineId
    ) => {
      if (!cartId) {
        return;
      }

      setCartLoading(
        true
      );

      setCartMessage(
        ""
      );

      try {
        const result =
          await removeCartItem(
            cartId,
            lineId
          );

        if (result.success) {
          setCart(
            result.cart
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
        setCartLoading(
          false
        );
      }
    };


  // ============================================================
  // APPLY PROMOTION
  // ============================================================

  const handleApplyPromotion =
    async (
      discountCode
    ) => {
      if (!cartId) {
        return;
      }

      setCartLoading(
        true
      );

      setCartMessage(
        ""
      );

      try {
        const result =
          await applyPromotion(
            cartId,
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
        setCartLoading(
          false
        );
      }
    };


  // ============================================================
  // REFRESH CART
  // ============================================================
  //
  // This currently refreshes the in-memory UI cart.
  //
  // Once cart REST endpoints are migrated to session_id,
  // refreshCart should resolve the backend cart using session_id
  // instead of passing Shopify cartId.
  // ============================================================

  const refreshCart =
    async () => {
      if (!cartId) {
        return;
      }

      try {
        const result =
          await getCart(
            cartId
          );

        if (
          result.success &&
          result.cart
        ) {
          setCart(
            result.cart
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
  // UI
  // ============================================================

  return (
    <div>

      {/* ======================================================
          HEADER
          ====================================================== */}

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


      {/* ======================================================
          STATUS MESSAGE
          ====================================================== */}

      {cartMessage && (
        <div className="status-message">
          {cartMessage}
        </div>
      )}


      {/* ======================================================
          CART LOADING
          ====================================================== */}

      {cartLoading && (
        <div className="loading-message">
          Updating cart...
        </div>
      )}


      {/* ======================================================
          MAIN COMMERCE LAYOUT
          ====================================================== */}

      <main className="commerce-layout">

        {/* ====================================================
            PRODUCT CATALOG
            ==================================================== */}

        <section className="catalog-section">

          <ProductPage
            onAddToCart={
              handleAddToCart
            }
          />

        </section>


        {/* ====================================================
            CART
            ==================================================== */}

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


        {/* ====================================================
            CHAT
            ==================================================== */}

        <section className="chat-section">

          <ChatWindow
            onCartChanged={
              refreshCart
            }
          />

        </section>

      </main>

    </div>
  );
}


export default CommercePage;