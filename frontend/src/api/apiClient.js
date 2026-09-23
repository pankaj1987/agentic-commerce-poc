import axios from "axios";

const apiClient = axios.create({
  baseURL:
    import.meta.env.VITE_API_BASE_URL ||
    "http://127.0.0.1:8000",
  headers: {
    "Content-Type": "application/json",
  },
});

// Phase 5A local-POC authentication only.
// In production these identity headers MUST be injected by a trusted gateway
// after validating an OIDC/JWT token. Never trust browser-asserted IDs there.
apiClient.interceptors.request.use((config) => {
  const userId =
    import.meta.env.VITE_DEV_USER_ID ||
    "demo-user-1";

  const shopifyCustomerId =
    import.meta.env.VITE_DEV_SHOPIFY_CUSTOMER_ID;

  config.headers["X-User-Id"] = userId;
  config.headers["X-User-Roles"] = "customer";

  if (shopifyCustomerId) {
    config.headers["X-Shopify-Customer-Id"] = shopifyCustomerId;
  }

  return config;
});

export default apiClient;
