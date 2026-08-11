import { useEffect } from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { useAuthStore } from "@/store/auth.store";
import api from "@/lib/api";
import { getAccessToken, clearTokens } from "@/lib/auth";

// Layouts
import { AppShell } from "@/components/layout/AppShell";
import { ProtectedRoute } from "@/components/shared/ProtectedRoute";

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
      {/* Auth Public Routes */}
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />

      {/* Private App Routes inside AppShell */}
      <Route element={<ProtectedRoute />}>
        <Route element={<AppShell />}>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/risk" element={<RiskPage />} />
          <Route path="/copilot" element={<CopilotPage />} />
          <Route path="/stress" element={<StressTestPage />} />
          <Route path="/graph" element={<GraphPage />} />
          <Route path="/audit" element={<AuditPage />} />
          <Route path="/borrowers" element={<BorrowersPage />} />
          <Route path="/loans" element={<LoansPage />} />
          <Route path="/uploads" element={<UploadsPage />} />
          <Route path="/documents/:agreementId" element={<DocumentDetailPage />} />
        </Route>
      </Route>

      {/* Default Catch-All */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
