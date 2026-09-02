import apiClient from "./apiClient";


export const searchProducts = async (
  query,
  maxPrice = null
) => {
  const request = {
    query,
  };

  if (maxPrice !== null && maxPrice !== "") {
    request.max_price = Number(maxPrice);
  }

  const response = await apiClient.post(
    "/api/products/search",
    request
  );

  return response.data;
};