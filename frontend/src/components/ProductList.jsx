import ProductCard from "./ProductCard";


function ProductList({
  products,
  onAddToCart,
}) {
  if (!products || products.length === 0) {
    return (
      <div className="empty-state">
        No products found.
      </div>
    );
  }

  return (
    <div className="product-list">

      {products.map((product, index) => (
        <ProductCard
          key={product.id || index}
          product={product}
          onAddToCart={onAddToCart}
        />
      ))}

    </div>
  );
}

export default ProductList;