import { useEffect } from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { useAuthStore } from "@/store/auth.store";
import api from "@/lib/api";
import { getAccessToken, clearTokens } from "@/lib/auth";

// Layouts
import { AppShell } from "@/components/layout/AppShell";
import { ProtectedRoute } from "@/components/shared/ProtectedRoute";

// Public Pages
import { LandingPage } from "@/pages/landing/LandingPage";

// Auth Pages
import { LoginPage } from "@/pages/auth/LoginPage";
import { RegisterPage } from "@/pages/auth/RegisterPage";

// Dashboard & Intelligence Pages
import DashboardPage from "@/pages/dashboard/DashboardPage";
import RiskPage from "@/pages/risk/RiskPage";
import CopilotPage from "@/pages/copilot/CopilotPage";
import StressTestPage from "@/pages/stress/StressTestPage";
import GraphPage from "@/pages/graph/GraphPage";
import BorrowersPage from "@/pages/borrowers/BorrowersPage";
import LoansPage from "@/pages/loans/LoansPage";
import UploadsPage from "@/pages/uploads/UploadsPage";
import DocumentDetailPage from "@/pages/documents/DocumentDetailPage";
import AuditPage from "@/pages/audit/AuditPage";
import OrganizationSettingsPage from "@/pages/settings/OrganizationSettingsPage";

export default function App() {
  const setUser = useAuthStore((state) => state.setUser);
  const setLoading = useAuthStore((state) => state.setLoading);

  useEffect(() => {
    async function loadSession() {
      const token = getAccessToken();
      if (!token) {
        setLoading(false);
        return;
      }

      try {
        const res = await api.get("/api/v1/auth/me");
        setUser(res.data);
      } catch (err) {
        console.error("Token session restoration failed", err);
        clearTokens();
        setUser(null);
      } finally {
        setLoading(false);
      }
    }
    loadSession();
  }, [setUser, setLoading]);

  return (
    <Routes>
      {/* Public Landing Page */}
      <Route path="/" element={<LandingPage />} />

      {/* Auth Public Routes */}
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />

      {/* Private App Routes inside AppShell — all under /app/* */}
      <Route element={<ProtectedRoute />}>
        <Route element={<AppShell />}>
          <Route path="/app" element={<DashboardPage />} />
          <Route path="/app/risk" element={<RiskPage />} />
          <Route path="/app/copilot" element={<CopilotPage />} />
          <Route path="/app/stress" element={<StressTestPage />} />
          <Route path="/app/graph" element={<GraphPage />} />
          <Route path="/app/audit" element={<AuditPage />} />
          <Route path="/app/borrowers" element={<BorrowersPage />} />
          <Route path="/app/loans" element={<LoansPage />} />
          <Route path="/app/uploads" element={<UploadsPage />} />
          <Route path="/app/documents/:agreementId" element={<DocumentDetailPage />} />
          <Route path="/app/settings/organization" element={<OrganizationSettingsPage />} />
        </Route>
      </Route>

      {/* Default Catch-All */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
