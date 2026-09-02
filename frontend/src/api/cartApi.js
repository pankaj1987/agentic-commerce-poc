import apiClient from "./apiClient";


// ============================================================
// CREATE CART
// POST /api/cart
// ============================================================

export const createCart = async () => {
  const response =
    await apiClient.post(
      "/api/cart"
    );

  return response.data;
};


// ============================================================
// GET CART
// GET /api/cart?cart_id=...
// ============================================================

export const getCart = async (
  cartId
) => {
  const response =
    await apiClient.get(
      "/api/cart",
      {
        params: {
          cart_id: cartId,
        },
      }
    );

  return response.data;
};


// ============================================================
// ADD ITEM
// POST /api/cart/items
// ============================================================

export const addCartItem = async (
  cartId,
  variantId,
  quantity = 1
) => {
  const response =
    await apiClient.post(
      "/api/cart/items",
      {
        cart_id: cartId,
        variant_id: variantId,
        quantity,
      }
    );

  return response.data;
};


// ============================================================
// UPDATE ITEM QUANTITY
// PATCH /api/cart/items
// ============================================================

export const updateCartItem = async (
  cartId,
  lineId,
  quantity
) => {
  const response =
    await apiClient.patch(
      "/api/cart/items",
      {
        cart_id: cartId,
        line_id: lineId,
        quantity,
      }
    );

  return response.data;
};


// ============================================================
// REMOVE ITEM
// POST /api/cart/items/remove
// ============================================================

export const removeCartItem = async (
  cartId,
  lineId
) => {
  const response =
    await apiClient.post(
      "/api/cart/items/remove",
      {
        cart_id: cartId,
        line_id: lineId,
      }
    );

  return response.data;
};


// ============================================================
// APPLY PROMOTION
// POST /api/cart/promotion
// ============================================================

export const applyPromotion = async (
  cartId,
  discountCode
) => {
  const response =
    await apiClient.post(
      "/api/cart/promotion",
      {
        cart_id: cartId,
        discount_code: discountCode,
      }
    );

  return response.data;
};