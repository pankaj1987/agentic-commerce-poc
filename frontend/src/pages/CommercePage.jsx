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
  const [cartId, setCartId] =
    useState(null);

  const [cart, setCart] =
    useState(null);

  const [cartLoading, setCartLoading] =
    useState(false);

  const [cartMessage, setCartMessage] =
    useState("");

  // Prevent duplicate cart initialization in React StrictMode.
  const cartInitializationStarted =
    useRef(false);


  // ============================================================
  // INITIALIZE CART SESSION
  //
  // On page load:
  // 1. Prevent duplicate execution in React StrictMode
  // 2. Check localStorage for an existing Shopify cart ID
  // 3. If found, try to restore that cart
  // 4. If not found or invalid, create a new cart
  // ============================================================

  useEffect(() => {
    if (cartInitializationStarted.current) {
      return;
    }

    cartInitializationStarted.current = true;

    initializeCartSession();
  }, []);


  const initializeCartSession = async () => {
    const existingCartId =
      localStorage.getItem(
        "shopify_cart_id"
      );

    if (existingCartId) {
      console.log(
        "Existing Shopify cart ID found in localStorage."
      );

      await loadExistingCart(
        existingCartId
      );
    } else {
      console.log(
        "No existing cart found. Creating a new Shopify cart."
      );

      await initializeCart();
    }
  };


  // ============================================================
  // LOAD EXISTING CART
  // ============================================================

  const loadExistingCart = async (
    existingCartId
  ) => {
    setCartLoading(true);
    setCartMessage("");

    try {
      const result =
        await getCart(
          existingCartId
        );

      if (
        result.success &&
        result.cart
      ) {
        setCartId(
          existingCartId
        );

        setCart(
          result.cart
        );

        console.log(
          "Existing Shopify cart restored successfully."
        );

        return;
      }

      console.warn(
        "Stored Shopify cart is no longer valid."
      );

      localStorage.removeItem(
        "shopify_cart_id"
      );

      await initializeCart();

    } catch (error) {
      console.error(
        "Unable to restore existing cart:",
        error
      );

      localStorage.removeItem(
        "shopify_cart_id"
      );

      await initializeCart();

    } finally {
      setCartLoading(false);
    }
  };


  // ============================================================
  // CREATE NEW CART
  // ============================================================

  const initializeCart = async () => {
    setCartLoading(true);
    setCartMessage("");

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

        localStorage.setItem(
          "shopify_cart_id",
          result.cart.id
        );

        console.log(
          "New Shopify cart created and saved to localStorage."
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
      setCartLoading(false);
    }
  };


  // ============================================================
  // ADD TO CART
  // ============================================================

  const handleAddToCart = async (
    variantId,
    quantity
  ) => {
    if (!cartId) {
      setCartMessage(
        "Shopping cart is not ready yet."
      );

      return;
    }

    setCartLoading(true);
    setCartMessage("");

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
      setCartLoading(false);
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

      setCartLoading(true);
      setCartMessage("");

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
        setCartLoading(false);
      }
    };


  // ============================================================
  // REMOVE ITEM
  // ============================================================

  const handleRemove =
    async (lineId) => {
      if (!cartId) {
        return;
      }

      setCartLoading(true);
      setCartMessage("");

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
        setCartLoading(false);
      }
    };


  // ============================================================
  // APPLY PROMOTION
  // ============================================================

  const handleApplyPromotion =
    async (discountCode) => {
      if (!cartId) {
        return;
      }

      setCartLoading(true);
      setCartMessage("");

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
        setCartLoading(false);
      }
    };


  // ============================================================
    //Refresh cart data from the server to ensure the UI is up-to-date.
  // ============================================================

  const refreshCart = async () => {
  if (!cartId) {
    return;
  }

  try {
    const result = await getCart(cartId);

    if (
      result.success &&
      result.cart
    ) {
      setCart(result.cart);
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
            cartId={cartId}
            onCartChanged={refreshCart}
          />

        </section>

      </main>

    </div>
  );
}

export default CommercePage;