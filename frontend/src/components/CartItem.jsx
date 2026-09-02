function CartItem({
  item,
  onUpdateQuantity,
  onRemove,
}) {
  const merchandise = item.merchandise || {};

  const productTitle =
    merchandise.product?.title ||
    merchandise.title ||
    "Product";

  return (
    <div className="cart-item">

      <div className="cart-item-info">

        <strong>
          {productTitle}
        </strong>

        {merchandise.title && (
          <div>
            {merchandise.title}
          </div>
        )}

      </div>

      <div className="quantity-controls">

        <button
          disabled={item.quantity <= 1}
          onClick={() =>
            onUpdateQuantity(
              item.id,
              item.quantity - 1
            )
          }
        >
          -
        </button>

        <span>
          {item.quantity}
        </span>

        <button
          onClick={() =>
            onUpdateQuantity(
              item.id,
              item.quantity + 1
            )
          }
        >
          +
        </button>

      </div>

      <button
        className="remove-button"
        onClick={() =>
          onRemove(item.id)
        }
      >
        Remove
      </button>

    </div>
  );
}

export default CartItem;