import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import {
  Sparkles, AlertTriangle,
  FileText, CheckCircle2,
  ArrowUpRight, ShieldAlert,
  Activity, Zap, BrainCircuit, Building2
} from "lucide-react";
import {
  LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer
} from "recharts";
import { useAuthStore } from "@/store/auth.store";
import { useCompanyStore } from "@/store/company.store";
import api from "@/lib/api";

interface RecentDoc {
  agreement_id: string;
  loan_id: string;
  file_path: string;
  document_type: string;
  processing_status: string;
  upload_date: string;
}

interface CompanyHealth {
  score: number;
  category: string;
  breakdown: {
    financial_score: number;
    compliance_score: number;
    liquidity_score: number;
    leverage_score: number;
    trend_score: number;
  };
  history: { month?: string; date_label?: string; calculated_at?: string; score: number }[];
}

interface AlertItem {
  id: string;
  severity: string;
  title: string;
  message: string;
  created_at: string;
}

interface TrendItem {
  month: string;
  score: number;
}

export default function DashboardPage() {
  const { user } = useAuthStore();
  const navigate = useNavigate();
  const { selectedCompanyId, selectedCompany } = useCompanyStore();

  const [companyHealth, setCompanyHealth] = useState<CompanyHealth | null>(null);
  const [recentDocs, setRecentDocs] = useState<RecentDoc[]>([]);
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [trendData, setTrendData] = useState<TrendItem[]>([]);
  const [covenantBreachCount, setCovenantBreachCount] = useState(0);
  // MEDIUM-2: Real facility count from PostgreSQL, not inferred from document count.
  // null = data unavailable (API error); number = authoritative DB count (0 is valid).
  const [activeFacilitiesCount, setActiveFacilitiesCount] = useState<number | null>(null);

  useEffect(() => {
    if (!selectedCompanyId) return;

    async function loadCompanyDashboard() {
      try {
        const [healthRes, alertsRes, covsRes, loanCountRes] = await Promise.all([
          api.get(`/api/v1/risk/health/${selectedCompanyId}`).catch(() => ({ data: null })),
          api.get(`/api/v1/alerts/?borrower_id=${selectedCompanyId}`).catch(() => ({ data: [] })),
          api.get(`/api/v1/risk/covenants/${selectedCompanyId}`).catch(() => ({ data: [] })),
          // MEDIUM-2: Authoritative facility count from PostgreSQL.
          api.get(`/api/v1/loans/count?borrower_id=${selectedCompanyId}`).catch(() => ({ data: null })),
        ]);

        if (healthRes.data) {
          setCompanyHealth(healthRes.data);
          const historyArr = healthRes.data.history || [];
          const formattedTrend = historyArr.map((h: any) => ({
            month: h.date_label || (h.calculated_at ? new Date(h.calculated_at).toLocaleDateString("en-US", { month: "short", day: "numeric" }) : "Score"),
            score: h.score,
          }));
          setTrendData(formattedTrend);
        } else {
          setCompanyHealth(null);
          setTrendData([]);
        }

        const alertsList = alertsRes.data || [];
        setAlerts(alertsList);

        const covsList = covsRes.data || [];
        const breaches = covsList.filter((c: any) => ["breach", "critical"].includes(c.status)).length;
        setCovenantBreachCount(breaches);

        // MEDIUM-2: Set real facility count. null if API failed (shows N/A).
        if (loanCountRes.data && typeof loanCountRes.data.count === "number") {
          setActiveFacilitiesCount(loanCountRes.data.count);
        } else {
          setActiveFacilitiesCount(null);
        }

        // Fetch ingested documents directly for selected borrower
        try {
          const docsRes = await api.get(`/api/v1/documents/borrower/${selectedCompanyId}`);
          setRecentDocs(docsRes.data || []);
        } catch {
          setRecentDocs([]);
        }
      } catch (e) {
        console.error("Company dashboard load error", e);
      }
    }

    loadCompanyDashboard();
  }, [selectedCompanyId]);

  const companyName = selectedCompany?.company_name || "Company Entity";
  // RULE: null score ≠ 0 score. Use null to distinguish "no data" from "calculated zero".
  const healthScore: number | null = companyHealth?.score ?? null;
  const healthCategory = companyHealth?.category ? companyHealth.category.toUpperCase() : "NO DATA";

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-3xl font-bold tracking-tight">Credit Risk Intelligence Dashboard</h1>
            <span className="px-3 py-1 bg-primary/10 text-primary border border-primary/20 rounded-full text-xs font-semibold flex items-center gap-1.5">
              <Building2 className="w-3.5 h-3.5" /> {companyName}
            </span>
          </div>
          <p className="text-muted-foreground mt-1">
            Welcome back, <strong className="text-foreground">{user?.name}</strong>. Real-time covenant and risk monitoring for <strong>{companyName}</strong>.
          </p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={() => navigate("/copilot")}
            className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground text-sm font-semibold rounded-lg hover:bg-primary/90 transition-all shadow-md"
          >
            <BrainCircuit className="w-4 h-4" /> Ask AI Copilot
          </button>
          <button
            onClick={() => navigate("/uploads")}
            className="flex items-center gap-2 px-4 py-2 bg-card border border-border text-foreground text-sm font-semibold rounded-lg hover:bg-muted/50 transition-all"
          >
            <FileText className="w-4 h-4" /> Upload / SEC EDGAR
          </button>
        </div>
      </div>

      {/* Metric Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        {/* Borrower Health Score */}
        <div className="bg-card border border-border p-6 rounded-2xl shadow-sm relative overflow-hidden">
          <div className="flex justify-between items-center">
            <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Borrower Health Score</span>
            <span className={`px-2.5 py-0.5 text-xs font-bold rounded-full border ${
              healthScore != null && healthScore >= 75
                ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                : healthScore != null && healthScore >= 60
                ? "bg-blue-500/10 text-blue-400 border-blue-500/20"
                : healthScore != null && healthScore > 0
                ? "bg-amber-500/10 text-amber-400 border-amber-500/20"
                : "bg-muted text-muted-foreground border-border"
            }`}>
              {healthCategory}
            </span>
          </div>
          <div className="flex items-baseline gap-2 mt-4">
            <span className="text-4xl font-extrabold text-foreground">
              {companyHealth ? healthScore : "--"}
            </span>
            <span className="text-sm font-medium text-muted-foreground">/ 100</span>
          </div>
          <p className="text-xs text-muted-foreground mt-3 flex items-center justify-between border-t border-border/50 pt-2">
            <span>Financial Performance</span>
            <span className="font-semibold text-foreground">{companyHealth?.breakdown?.financial_score ? `${companyHealth.breakdown.financial_score.toFixed(1)}/100` : "--"}</span>
          </p>
        </div>

        {/* Monitored Facilities */}
        <div className="bg-card border border-border p-6 rounded-2xl shadow-sm relative overflow-hidden">
          <div className="flex justify-between items-center">
            <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Active Facilities</span>
            <div className="p-2 bg-primary/10 text-primary rounded-lg">
              <ShieldAlert className="w-4 h-4" />
            </div>
          </div>
          <div className="flex items-baseline gap-2 mt-4">
            {/* MEDIUM-2: Real facility count from GET /api/v1/loans/count.
                null = API unavailable → show "N/A"; number = authoritative DB count. */}
            <span className="text-4xl font-extrabold text-foreground">
              {activeFacilitiesCount !== null ? activeFacilitiesCount : "N/A"}
            </span>
            <span className="text-sm text-muted-foreground">Monitored Facilities</span>
          </div>
          <p className="text-xs text-muted-foreground mt-3 border-t border-border/50 pt-2">
            Sector: <strong className="text-foreground">{selectedCompany?.sector || "N/A"}</strong>
          </p>
        </div>

        {/* Covenant Breaches */}
        <div className="bg-card border border-border p-6 rounded-2xl shadow-sm relative overflow-hidden">
          <div className="flex justify-between items-center">
            <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Covenant Breaches</span>
            <div className={`p-2 rounded-lg ${covenantBreachCount > 0 ? "bg-red-500/10 text-red-400" : "bg-emerald-500/10 text-emerald-400"}`}>
              <AlertTriangle className="w-4 h-4" />
            </div>
          </div>
          <div className="flex items-baseline gap-2 mt-4">
            <span className={`text-4xl font-extrabold ${covenantBreachCount > 0 ? "text-red-400" : "text-foreground"}`}>
              {covenantBreachCount}
            </span>
            <span className="text-sm text-muted-foreground">Active Breaches</span>
          </div>
          <p className="text-xs text-muted-foreground mt-3 border-t border-border/50 pt-2">
            Status: <strong className={covenantBreachCount > 0 ? "text-red-400" : "text-emerald-400"}>{covenantBreachCount > 0 ? "Action Required" : "Monitored Clean"}</strong>
          </p>
        </div>

        {/* System Alerts */}
        <div className="bg-card border border-border p-6 rounded-2xl shadow-sm relative overflow-hidden">
          <div className="flex justify-between items-center">
            <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Company Alerts</span>
            <div className="p-2 bg-purple-500/10 text-purple-400 rounded-lg">
              <Zap className="w-4 h-4" />
            </div>
          </div>
          <div className="flex items-baseline gap-2 mt-4">
            <span className="text-4xl font-extrabold text-foreground">{alerts.length}</span>
            <span className="text-sm text-muted-foreground">Warnings</span>
          </div>
          <p className="text-xs text-muted-foreground mt-3 border-t border-border/50 pt-2">
            Severity: <strong className="text-foreground">{alerts.filter(a => a.severity === "critical").length} Critical</strong>
          </p>
        </div>
      </div>

      {/* AI Risk Insights & Alerts List */}
      <div className="bg-card border border-border p-6 rounded-2xl shadow-sm space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="p-2 bg-primary/20 text-primary rounded-lg border border-primary/30">
              <Sparkles className="w-4 h-4" />
            </div>
            <div>
              <h3 className="font-bold text-foreground">AI Risk Insights & Live Alerts — {companyName}</h3>
              <p className="text-xs text-muted-foreground">Real-time alerts for the selected company entity</p>
            </div>
          </div>
        </div>

        {alerts.length === 0 ? (
          <div className="py-12 text-center text-muted-foreground space-y-2 bg-muted/20 border border-dashed border-border rounded-xl">
            <CheckCircle2 className="w-8 h-8 mx-auto opacity-40 text-emerald-400" />
            <p className="font-semibold text-sm">No risk alerts recorded for {companyName}</p>
            <p className="text-xs">Upload a loan agreement or SEC EDGAR filing to trigger AI risk analysis.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {alerts.slice(0, 4).map((alert) => (
              <div key={alert.id} className="p-4 bg-muted/30 border border-border rounded-xl space-y-1">
                <div className="flex items-center gap-2 text-xs font-semibold text-red-400">
                  <AlertTriangle className="w-3.5 h-3.5" />
                  <span>[{companyName}] {alert.title}</span>
                </div>
                <p className="text-xs text-muted-foreground leading-relaxed">{alert.message}</p>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Trend & Distribution Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Health Score Trajectory */}
        <div className="lg:col-span-2 bg-card border border-border p-6 rounded-2xl shadow-sm space-y-4">
          <div className="flex justify-between items-center">
            <div>
              <h3 className="font-bold text-foreground">Borrower Health Score Trajectory</h3>
              <p className="text-xs text-muted-foreground">Historical health calculated for {companyName}</p>
            </div>
            <button
              onClick={() => navigate("/risk")}
              className="text-xs font-semibold text-primary hover:underline flex items-center gap-1"
            >
              Risk Deep-Dive <ArrowUpRight className="w-3 h-3" />
            </button>
          </div>

          {trendData.length === 0 ? (
            <div className="h-64 flex flex-col items-center justify-center text-muted-foreground bg-muted/20 border border-dashed border-border rounded-xl">
              <Activity className="w-8 h-8 opacity-30 mb-2" />
              <p className="font-semibold text-sm">No historical score records for {companyName} yet</p>
              <p className="text-xs">Upload financial documents to begin score tracking.</p>
            </div>
          ) : (
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={trendData}>
                  <XAxis dataKey="month" stroke="#888888" fontSize={12} tickLine={false} axisLine={false} />
                  <YAxis domain={[0, 100]} stroke="#888888" fontSize={12} tickLine={false} axisLine={false} />
                  <Tooltip
                    contentStyle={{ backgroundColor: "#1e1e2d", borderColor: "#33334d", borderRadius: "12px", color: "#fff" }}
                  />
                  <Line type="monotone" dataKey="score" stroke="#10b981" strokeWidth={3} dot={{ r: 4, fill: "#10b981" }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>

        {/* Recent Ingested Documents */}
        <div className="bg-card border border-border p-6 rounded-2xl shadow-sm space-y-4">
          <h3 className="font-bold text-foreground">Ingested Documents</h3>
          <p className="text-xs text-muted-foreground">Recent files uploaded for {companyName}</p>

          {recentDocs.length === 0 ? (
            <div className="py-12 text-center text-muted-foreground space-y-2 bg-muted/20 border border-dashed border-border rounded-xl">
              <FileText className="w-8 h-8 mx-auto opacity-30" />
              <p className="font-semibold text-sm">No documents ingested for {companyName}</p>
              <button
                onClick={() => navigate("/uploads")}
                className="text-xs text-primary font-semibold hover:underline mt-1 block"
              >
                Go to Ingestion & SEC
              </button>
            </div>
          ) : (
            <div className="space-y-3">
              {recentDocs.map((doc) => (
                <div
                  key={doc.agreement_id}
                  onClick={() => navigate(`/documents/${doc.agreement_id}`)}
                  className="p-3 bg-muted/30 border border-border rounded-xl hover:border-primary/40 cursor-pointer transition-all flex items-center justify-between"
                >
                  <div className="flex items-center gap-2 overflow-hidden">
                    <FileText className="w-4 h-4 text-primary shrink-0" />
                    <span className="text-xs font-semibold text-foreground truncate">
                      {doc.file_path.split("/").pop() ?? doc.agreement_id.slice(0, 8)}
                    </span>
                  </div>
                  <span className="text-[10px] px-2 py-0.5 rounded-full font-bold uppercase bg-emerald-500/10 text-emerald-400">
                    {doc.processing_status}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
