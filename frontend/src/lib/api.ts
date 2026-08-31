import axios from "axios";
import { getAccessToken, clearTokens } from "@/lib/auth";

const api = axios.create({
  // Empty baseURL: Vite dev proxy forwards /api/* → http://localhost:8000
  // In production, set VITE_API_BASE_URL to your deployed backend URL
  baseURL: (import.meta as any).env?.VITE_API_BASE_URL || "",
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor: inject access token
api.interceptors.request.use(
  (config) => {
    const token = getAccessToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor: handle token refresh or redirect on 401
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    const url = originalRequest?.url || "";
    const isAuthEndpoint =
      url.includes("/auth/login") ||
      url.includes("/auth/signup") ||
      url.includes("/auth/accept-invite") ||
      url.includes("/auth/verify-invite");

    // Only redirect to /login on 401 if it's a private app endpoint and we're not already on an auth page
    if (error.response?.status === 401 && !originalRequest?._retry && !isAuthEndpoint) {
      originalRequest._retry = true;
      clearTokens();
      if (!window.location.pathname.startsWith("/login") && !window.location.pathname.startsWith("/register")) {
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

export default api;
