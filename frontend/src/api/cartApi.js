import apiClient from "./apiClient";


// The browser sends only the public commerce session ID.
// Shopify cart IDs stay server-side.

export const createCart = async (
  sessionId = null
) => {
  const response = await apiClient.post(
    "/api/cart",
    {
      session_id: sessionId || null,
    }
  );

  return response.data;
};


export const getCart = async (
  sessionId
) => {
  const response = await apiClient.get(
    "/api/cart",
    {
      params: {
        session_id: sessionId,
      },
    }
  );

  return response.data;
};


export const addCartItem = async (
  sessionId,
  variantId,
  quantity = 1
) => {
  const response = await apiClient.post(
    "/api/cart/items",
    {
      session_id: sessionId,
      variant_id: variantId,
      quantity,
    }
  );

  return response.data;
};


export const updateCartItem = async (
  sessionId,
  lineId,
  quantity
) => {
  const response = await apiClient.patch(
    "/api/cart/items",
    {
      session_id: sessionId,
      line_id: lineId,
      quantity,
    }
  );

  return response.data;
};


export const removeCartItem = async (
  sessionId,
  lineId
) => {
  const response = await apiClient.post(
    "/api/cart/items/remove",
    {
      session_id: sessionId,
      line_id: lineId,
    }
  );

  return response.data;
};


export const applyPromotion = async (
  sessionId,
  discountCode
) => {
  const response = await apiClient.post(
    "/api/cart/promotion",
    {
      session_id: sessionId,
      discount_code: discountCode,
    }
  );

  return response.data;
};
