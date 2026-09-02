import { useState } from "react";


function ProductCard({
  product,
  onAddToCart,
}) {
  const variants =
    product.variants?.nodes ||
    product.variants ||
    [];

  const [selectedVariantId, setSelectedVariantId] =
    useState(
      product.variant_id ||
      variants[0]?.id ||
      ""
    );

  const price =
    product.price?.amount ??
    product.priceRangeV2?.minVariantPrice?.amount ??
    "";

  const currency =
    product.price?.currency ??
    product.priceRangeV2?.minVariantPrice?.currencyCode ??
    "";

  const handleAdd = () => {
    if (!selectedVariantId) {
      alert(
        "No Shopify variant is available for this product."
      );
      return;
    }

    onAddToCart(
      selectedVariantId,
      1
    );
  };

  return (
    <div className="product-card">

      <h3>
        {product.title}
      </h3>

      {product.vendor && (
        <p className="product-brand">
          {product.vendor}
        </p>
      )}

      {product.description && (
        <p>
          {product.description}
        </p>
      )}

      {price && (
        <p className="product-price">
          {currency} {price}
        </p>
      )}

      {variants.length > 1 && (
        <select
          value={selectedVariantId}
          onChange={(event) =>
            setSelectedVariantId(
              event.target.value
            )
          }
        >
          {variants.map((variant) => (
            <option
              key={variant.id}
              value={variant.id}
            >
              {variant.title}
            </option>
          ))}
        </select>
      )}

      <button
        onClick={handleAdd}
        disabled={!selectedVariantId}
      >
        Add to Cart
      </button>

    </div>
  );
}

export default ProductCard;