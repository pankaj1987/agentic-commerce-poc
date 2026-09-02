import { useState } from "react";

import {
  searchProducts,
} from "../api/productApi";

import ProductList from "../components/ProductList";


function ProductPage({
  onAddToCart,
}) {
  const [query, setQuery] =
    useState("");

  const [maxPrice, setMaxPrice] =
    useState("");

  const [products, setProducts] =
    useState([]);

  const [loading, setLoading] =
    useState(false);

  const [error, setError] =
    useState("");

  const handleSearch = async () => {
    if (!query.trim()) {
      return;
    }

    setLoading(true);
    setError("");

    try {
      const result =
        await searchProducts(
          query.trim(),
          maxPrice
        );

      setProducts(
        result.products || []
      );

    } catch (error) {
      console.error(
        "Product search failed:",
        error
      );

      setError(
        "Unable to search products."
      );

    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="product-page">

      <h2>
        Product Search
      </h2>

      <div className="search-bar">

        <input
          value={query}
          placeholder="Search products..."
          onChange={(event) =>
            setQuery(
              event.target.value
            )
          }
        />

        <input
          type="number"
          value={maxPrice}
          placeholder="Max price"
          onChange={(event) =>
            setMaxPrice(
              event.target.value
            )
          }
        />

        <button
          onClick={handleSearch}
          disabled={loading}
        >
          {loading
            ? "Searching..."
            : "Search"}
        </button>

      </div>

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      {!loading && (
        <ProductList
          products={products}
          onAddToCart={
            onAddToCart
          }
        />
      )}

    </div>
  );
}

export default ProductPage;