import apiClient from "./apiClient";


export const sendChatMessage = async (
  message,
  cartId = null
) => {
  const request = {
    message,
  };

  if (cartId) {
    request.cart_id = cartId;
  }

  const response = await apiClient.post(
    "/api/chat",
    request
  );

  return response.data;
};