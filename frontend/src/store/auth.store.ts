import { create } from "zustand";
import { User } from "@/types";
import { setAccessToken, setRefreshToken, clearTokens } from "@/lib/auth";
import { useCompanyStore } from "@/store/company.store";

interface AuthState {
  user: User | null;
  token?: string | null;
  refreshToken?: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (user: User, accessToken: string, refreshToken: string) => void;
  logout: () => void;
  setUser: (user: User | null) => void;
  setLoading: (loading: boolean) => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: false,
  isLoading: true,
  login: (user, accessToken, refreshToken) => {
    setAccessToken(accessToken);
    setRefreshToken(refreshToken);
    // Reset selected company on new user login
    useCompanyStore.getState().clearCompanies();
    set({ user, token: accessToken, refreshToken, isAuthenticated: true, isLoading: false });
  },
  logout: () => {
    clearTokens();
    // Clear active company / organization context from storage & store
    useCompanyStore.getState().clearCompanies();
    localStorage.removeItem("selected_company_id");
    set({ user: null, token: null, refreshToken: null, isAuthenticated: false, isLoading: false });
  },
  setUser: (user) => set({ user, isAuthenticated: !!user, isLoading: false }),
  setLoading: (loading) => set({ isLoading: loading }),
}));
