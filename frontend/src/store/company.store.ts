import { create } from "zustand";
import api from "@/lib/api";

export interface Company {
  id: string;
  organization_id?: string;
  company_name: string;
  sector: string;
  country: string;
  risk_rating: { level: string; score: number };
}

interface RegisterPayload {
  company_name: string;
  sector: string;
  country: string;
  risk_level: string;    // LOW | MEDIUM | HIGH
  risk_score: number;    // 1-10
}

interface CompanyState {
  companies: Company[];
  selectedCompanyId: string;
  selectedCompany: Company | null;
  isRegisterModalOpen: boolean;
  loading: boolean;

  fetchCompanies: () => Promise<void>;
  setSelectedCompanyId: (id: string) => void;
  openRegisterModal: () => void;
  closeRegisterModal: () => void;
  registerCompany: (data: RegisterPayload) => Promise<Company>;
  clearCompanies: () => void;
}

// Read persisted selection
const persisted = localStorage.getItem("selected_company_id") ?? "";

export const useCompanyStore = create<CompanyState>((set, get) => ({
  companies: [],
  selectedCompanyId: persisted,
  selectedCompany: null,
  isRegisterModalOpen: false,
  loading: false,

  fetchCompanies: async () => {
    set({ loading: true });
    try {
      const res = await api.get("/api/v1/borrowers/");
      const companies: Company[] = res.data ?? [];
      set({ companies });

      const currentId = get().selectedCompanyId;
      let active = companies.find((c) => c.id === currentId) ?? null;

      if (!active && companies.length > 0) {
        active = companies[0];
        localStorage.setItem("selected_company_id", active.id);
      }
      set({ selectedCompanyId: active?.id ?? "", selectedCompany: active });
    } catch (e) {
      console.error("Failed to fetch companies", e);
    } finally {
      set({ loading: false });
    }
  },

  setSelectedCompanyId: (id) => {
    const active = get().companies.find((c) => c.id === id) ?? null;
    set({ selectedCompanyId: id, selectedCompany: active });
    localStorage.setItem("selected_company_id", id);
  },

  openRegisterModal: () => set({ isRegisterModalOpen: true }),
  closeRegisterModal: () => set({ isRegisterModalOpen: false }),

  clearCompanies: () => {
    set({ companies: [], selectedCompanyId: "", selectedCompany: null });
    localStorage.removeItem("selected_company_id");
  },

  registerCompany: async ({ company_name, sector, country, risk_level, risk_score }) => {
    set({ loading: true });
    try {
      // Fetch valid organization ID — never fall back to a hardcoded UUID.
      // If organizations cannot be retrieved, surface the error explicitly.
      const orgRes = await api.get("/api/v1/organizations/");
      if (!orgRes.data || orgRes.data.length === 0) {
        throw new Error(
          "No organization found. Please create an organization first before registering a borrower."
        );
      }
      const orgId: string = orgRes.data[0].id;

      const resB = await api.post("/api/v1/borrowers/", {
        organization_id: orgId,
        company_name,
        sector,
        country,
        risk_rating: { level: risk_level, score: risk_score },
      });
      const newBorrower: Company = resB.data;
      // NOTE: No auto-loan creation here.
      // Loans represent real credit facilities with real terms.
      // The user must create them explicitly via the Loans page.
      // A new borrower correctly starts with 0 loans.

      await get().fetchCompanies();
      get().setSelectedCompanyId(newBorrower.id);
      set({ isRegisterModalOpen: false });
      return newBorrower;
    } catch (err: any) {
      throw err;
    } finally {
      set({ loading: false });
    }
  },
}));
