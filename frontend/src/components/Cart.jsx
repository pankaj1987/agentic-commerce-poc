import { useState } from "react";

import CartItem from "./CartItem";


function Cart({
  cart,
  onUpdateQuantity,
  onRemove,
  onApplyPromotion,
}) {
  const [discountCode, setDiscountCode] =
    useState("");

  if (!cart) {
    return (
      <div className="cart-panel">
        <h2>Cart</h2>
        <p>No cart created yet.</p>
      </div>
    );
  }

  const lines =
    cart.lines?.nodes ||
    cart.lines ||
    [];

  const cost =
    cart.cost || {};

  const subtotal =
    cost.subtotalAmount;

  const total =
    cost.totalAmount;

  const handlePromotion = () => {
    if (!discountCode.trim()) {
      return;
    }

    onApplyPromotion(
      discountCode.trim()
    );
  };

  return (
    <div className="cart-panel">

      <h2>
        Shopping Cart
      </h2>

      <p>
        Items: {cart.totalQuantity || 0}
      </p>

      {lines.length === 0 ? (
        <p>
          Your cart is empty.
        </p>
      ) : (
        lines.map((item) => (
          <CartItem
            key={item.id}
            item={item}
            onUpdateQuantity={
              onUpdateQuantity
            }
            onRemove={onRemove}
          />
        ))
      )}

      {subtotal && (
        <p>
          Subtotal:{" "}
          {subtotal.currencyCode}{" "}
          {subtotal.amount}
        </p>
      )}

      {total && (
        <h3>
          Total:{" "}
          {total.currencyCode}{" "}
          {total.amount}
        </h3>
      )}

      <div className="promotion-section">

        <input
          type="text"
          placeholder="Promotion code"
          value={discountCode}
          onChange={(event) =>
            setDiscountCode(
              event.target.value
            )
          }
        />

        <button
          onClick={handlePromotion}
        >
          Apply
        </button>

      </div>

    </div>
  );
}

export default Cart;