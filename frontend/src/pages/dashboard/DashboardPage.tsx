import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import {
  Activity,
  ShieldAlert,
  AlertTriangle,
  Eye,
  ChevronRight,
  Brain,
} from "lucide-react";
import {
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  Tooltip,
  ResponsiveContainer
} from "recharts";

import { useAuthStore } from "@/store/auth.store";
import { useCompanyStore } from "@/store/company.store";
import api from "@/lib/api";

import { KpiCard } from "@/components/shared/KpiCard";
import { BorrowerCard } from "@/components/shared/BorrowerCard";
import { AlertCard } from "@/components/shared/AlertCard";
import { InsightCard } from "@/components/shared/InsightCard";
import { CardSkeleton } from "@/components/shared/LoadingSkeleton";
import { ErrorState } from "@/components/shared/ErrorState";
import { ImprovedEmptyState } from "@/components/shared/Explainer";
import { formatCompactCurrency } from "@/utils/format";

interface BorrowerItem {
  id: string;
  company_name: string;
  sector: string;
  country: string;
  risk_rating?: { level: string; score: number };
}

interface RiskHealth {
  score: number | null;
  category: string;
  breakdown?: {
    financial_score: number | null;
    compliance_score: number | null;
    liquidity_score: number | null;
    leverage_score: number | null;
    trend_score: number | null;
  };
}

interface LoanItem {
  id: string;
  borrower_id: string;
  principal_amount?: { amount: number; currency: string };
  interest_rate?: number;
  status?: string;
  is_archived?: boolean;
}

interface AlertItem {
  id: string;
  borrower_id?: string;
  title: string;
  message?: string;
  severity: string;
  created_at: string;
}

export default function DashboardPage() {
  const { user } = useAuthStore();
  const navigate = useNavigate();
  const { selectedCompanyId } = useCompanyStore();

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [borrowers, setBorrowers] = useState<BorrowerItem[]>([]);
  const [loans, setLoans] = useState<LoanItem[]>([]);
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [healthMap, setHealthMap] = useState<Record<string, RiskHealth>>({});
  const [covenantBreachCount, setCovenantBreachCount] = useState(0);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [borrowersRes, alertsRes, loansRes] = await Promise.all([
        api.get("/api/v1/borrowers/").catch(() => ({ data: [] })),
        api.get("/api/v1/alerts/").catch(() => ({ data: [] })),
        api.get("/api/v1/loans/").catch(() => ({ data: [] })),
      ]);

      const borrowerList: BorrowerItem[] = borrowersRes.data || [];
      const loanList: LoanItem[] = loansRes.data || [];
      const alertList: AlertItem[] = alertsRes.data || [];

      setBorrowers(borrowerList);
      setLoans(loanList);
      setAlerts(alertList);

      // Fetch health scores for each borrower
      const healthPromises = borrowerList.map((b) =>
        api
          .get(`/api/v1/risk/health/${b.id}`)
          .then((res) => ({ id: b.id, data: res.data }))
          .catch(() => ({ id: b.id, data: null }))
      );

      const healthResults = await Promise.all(healthPromises);
      const newHealthMap: Record<string, RiskHealth> = {};
      healthResults.forEach((item) => {
        if (item.data) {
          newHealthMap[item.id] = item.data;
        }
      });
      setHealthMap(newHealthMap);

      // Calculate total covenant breaches across portfolio
      if (selectedCompanyId) {
        const covRes = await api
          .get(`/api/v1/risk/covenants/${selectedCompanyId}`)
          .catch(() => ({ data: [] }));
        const breaches = (covRes.data || []).filter((c: any) =>
          ["breach", "critical"].includes(c.status)
        ).length;
        setCovenantBreachCount(breaches);
      } else {
        setCovenantBreachCount(0);
      }
    } catch (err: any) {
      console.error("Dashboard data load error:", err);
      setError("Failed to load portfolio metrics.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [selectedCompanyId]);

  // Compute portfolio statistics
  const totalBorrowers = borrowers.length;
  const highRiskCount = borrowers.filter(
    (b) =>
      b.risk_rating?.level === "HIGH" ||
      healthMap[b.id]?.category?.toUpperCase().includes("HIGH")
  ).length;
  const watchCount = borrowers.filter(
    (b) =>
      b.risk_rating?.level === "MEDIUM" ||
      healthMap[b.id]?.category?.toUpperCase().includes("WATCH") ||
      healthMap[b.id]?.category?.toUpperCase().includes("MODERATE")
  ).length;
  const lowRiskCount = borrowers.filter(
    (b) =>
      b.risk_rating?.level === "LOW" ||
      healthMap[b.id]?.category?.toUpperCase().includes("LOW") ||
      healthMap[b.id]?.category?.toUpperCase().includes("GOOD")
  ).length;

  const validScores = Object.values(healthMap)
    .map((h) => h.score)
    .filter((s): s is number => s !== null && s !== undefined);

  const avgPortfolioHealth =
    validScores.length > 0
      ? Math.round(
          validScores.reduce((acc, curr) => acc + curr, 0) / validScores.length
        )
      : null;

  // Donut Chart Data — 100% computed from real borrower risk levels
  const donutData = totalBorrowers > 0
    ? [
        { name: "High Risk", value: highRiskCount, color: "#EF4444" },
        { name: "Watch", value: watchCount, color: "#F97316" },
        { name: "Low Risk", value: lowRiskCount, color: "#10B981" },
      ].filter((d) => d.value > 0)
    : [{ name: "No Borrowers", value: 1, color: "#E5E7EB" }];

  // Active loans (excluding archived)
  const activeLoans = loans.filter((l) => l.is_archived !== true);

  // Group exposures by currency
  const currencyTotals = activeLoans.reduce<Record<string, number>>((acc, l) => {
    const amt = l.principal_amount?.amount ? Number(l.principal_amount.amount) : 0;
    const cur = (l.principal_amount?.currency || "USD").toUpperCase();
    acc[cur] = (acc[cur] || 0) + amt;
    return acc;
  }, {});

  const distinctCurrencies = Object.keys(currencyTotals);
  const primaryCurrency = distinctCurrencies[0] || "USD";

  // Formatted exposure adhering to native currency
  const formattedExposure =
    activeLoans.length === 0
      ? "N/A"
      : distinctCurrencies.length === 1
      ? formatCompactCurrency(currencyTotals[primaryCurrency], primaryCurrency)
      : distinctCurrencies
          .map((c) => formatCompactCurrency(currencyTotals[c], c))
          .join(" + ");

  // Exposure chart data based on actual facilities with native currency
  const exposureData = activeLoans.length > 0
    ? activeLoans.slice(0, 7).map((l, idx) => {
        const amt = l.principal_amount?.amount ? Number(l.principal_amount.amount) : 0;
        const cur = (l.principal_amount?.currency || primaryCurrency).toUpperCase();
        return {
          label: `Fac #${idx + 1}`,
          val: amt,
          formatted: formatCompactCurrency(amt, cur),
          currency: cur,
        };
      })
    : [
        { label: "—", val: 0, formatted: "N/A", currency: "USD" },
        { label: "—", val: 0, formatted: "N/A", currency: "USD" },
        { label: "—", val: 0, formatted: "N/A", currency: "USD" },
      ];

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="h-8 bg-gray-200 rounded w-1/4 animate-pulse" />
        <div className="grid grid-cols-1 md:grid-cols-4 gap-5">
          <CardSkeleton />
          <CardSkeleton />
          <CardSkeleton />
          <CardSkeleton />
        </div>
      </div>
    );
  }

  if (error) {
    return <ErrorState message={error} onRetry={loadData} />;
  }

  return (
    <div className="space-y-8 pb-10">
      {/* ── Page Welcome Header ────────────────────────────────────────── */}
      <div>
        <h1 className="text-2xl md:text-3xl font-bold text-[#111827] tracking-tight">
          Hello, {user?.name ? user.name.split(" ")[0] : "Analyst"} 👋
        </h1>
        <p className="text-xs md:text-sm font-medium text-[#6B7280] mt-1">
          Here's what's happening with your portfolio today.
        </p>
      </div>

      {/* ── TOP KPI ROW (4 Cards) ──────────────────────────────────────── */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <KpiCard
          title="Portfolio Health"
          subtitle="Overall borrower financial health."
          tooltip="Composite score (0–100) averaging health scores across all borrowers. Higher is better. Below 65 indicates watch-list conditions."
          value={avgPortfolioHealth !== null ? `${avgPortfolioHealth} / 100` : "N/A"}
          badgeText={
            avgPortfolioHealth !== null
              ? avgPortfolioHealth < 65
                ? "Watch"
                : "Good"
              : "No Data"
          }
          badgeType={
            avgPortfolioHealth !== null
              ? avgPortfolioHealth < 65
                ? "watch"
                : "success"
              : "neutral"
          }
          icon={Activity}
          iconBgColor="#E8ECFF"
          iconColor="#4F46E5"
          sparklineData={validScores.length >= 2 ? validScores.slice(0, 6) : undefined}
        />

        <KpiCard
          title="High Risk Borrowers"
          subtitle="Borrowers requiring immediate attention."
          tooltip="Count of borrowers classified as High Risk based on financial health scores, covenant status, and risk assessments."
          value={highRiskCount}
          trendText={totalBorrowers > 0 ? `${highRiskCount} of ${totalBorrowers} borrowers` : "0 in portfolio"}
          trendUp={highRiskCount > 0}
          icon={ShieldAlert}
          iconBgColor="#FEE2E2"
          iconColor="#EF4444"
        />

        <KpiCard
          title="Covenants At Risk"
          subtitle="Contractual conditions approaching or breached."
          tooltip="Number of financial covenants that are breached or critically close to their threshold. Covenant breaches can trigger credit events."
          value={covenantBreachCount}
          trendText={covenantBreachCount > 0 ? "Requires review" : "All compliant"}
          trendUp={covenantBreachCount > 0}
          icon={AlertTriangle}
          iconBgColor="#FFEDD5"
          iconColor="#F97316"
        />

        <KpiCard
          title="Watchlist"
          subtitle="Borrowers under active monitoring."
          tooltip="Borrowers flagged for elevated risk — not yet High Risk, but requiring closer monitoring due to deteriorating financial signals."
          value={watchCount}
          trendText={watchCount > 0 ? "Under monitoring" : "No watchlist items"}
          trendUp={false}
          icon={Eye}
          iconBgColor="#F3E8FF"
          iconColor="#9333EA"
        />
      </div>

      {/* ── SECOND ROW (Risk Distribution + Exposure + Recent Alerts) ─── */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Risk Distribution Donut (4 Cols) */}
        <div className="lg:col-span-4 bg-white rounded-2xl p-6 border border-[#EEF1F5] shadow-[0_4px_20px_rgba(17,24,39,0.04)] flex flex-col justify-between">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-bold text-[#111827]">Risk Distribution</h3>
              <p className="text-[10px] text-[#9CA3AF] mt-0.5">Borrowers by risk category</p>
            </div>
          </div>

          <div className="relative h-52 flex items-center justify-center">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={donutData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={80}
                  paddingAngle={totalBorrowers > 0 ? 4 : 0}
                  dataKey="value"
                >
                  {donutData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
              </PieChart>
            </ResponsiveContainer>
            {/* Donut Center Text */}
            <div className="absolute flex flex-col items-center justify-center text-center">
              <span className="text-2xl font-bold text-[#111827]">
                {totalBorrowers}
              </span>
              <span className="text-[11px] font-semibold text-[#6B7280]">Total</span>
            </div>
          </div>

          {/* Legend */}
          <div className="grid grid-cols-2 gap-2 mt-4 pt-4 border-t border-[#F3F4F6]">
            {totalBorrowers > 0 ? (
              donutData.map((item) => (
                <div key={item.name} className="flex items-center justify-between text-xs">
                  <div className="flex items-center gap-1.5">
                    <span className="w-2.5 h-2.5 rounded-full shrink-0" style={{ backgroundColor: item.color }} />
                    <span className="font-medium text-[#6B7280]">{item.name}</span>
                  </div>
                  <span className="font-bold text-[#111827]">{item.value}</span>
                </div>
              ))
            ) : (
              <p className="text-xs text-[#9CA3AF] col-span-2 text-center">No borrowers registered</p>
            )}
          </div>
        </div>

        {/* Middle: Portfolio Exposure Chart (5 Cols) */}
        <div className="lg:col-span-5 bg-white rounded-2xl p-6 border border-[#EEF1F5] shadow-[0_4px_20px_rgba(17,24,39,0.04)] flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold text-[#111827]">Portfolio Exposure</h3>
                <p className="text-[10px] text-[#9CA3AF] mt-0.5">
                  {activeLoans.length} active credit facilit{activeLoans.length !== 1 ? "ies" : "y"}
                </p>
              </div>
            </div>
            <div className="mt-2 flex items-baseline gap-3">
              <span className="text-3xl font-bold text-[#111827]">{formattedExposure}</span>
              {activeLoans.length > 0 && formattedExposure !== "N/A" && (
                <span className="text-xs font-semibold text-[#10B981]">Active Principal</span>
              )}
            </div>
          </div>

          <div className="h-44 mt-6 w-full">
            {activeLoans.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={exposureData} margin={{ top: 10, right: 0, left: -20, bottom: 0 }}>
                  <XAxis dataKey="label" axisLine={false} tickLine={false} tick={{ fontSize: 11, fill: "#9CA3AF" }} />
                  <Tooltip
                    cursor={{ fill: "#F3F4FF" }}
                    contentStyle={{ backgroundColor: "#111827", borderRadius: "8px", border: "none", color: "#FFF", fontSize: "12px" }}
                    formatter={(value: any, _name: any, item: any) => {
                      const cur = item?.payload?.currency || primaryCurrency;
                      return [formatCompactCurrency(value, cur), "Principal"];
                    }}
                  />
                  <Bar dataKey="val" fill="#C7D2FE" radius={[6, 6, 0, 0]} activeBar={{ fill: "#7C8DFB" }} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-xs text-[#9CA3AF]">
                No active loans in portfolio
              </div>
            )}
          </div>
        </div>

        {/* Right: Recent Alerts (3 Cols) */}
        <div className="lg:col-span-3 bg-white rounded-2xl p-5 border border-[#EEF1F5] shadow-[0_4px_20px_rgba(17,24,39,0.04)] flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <div>
                <h3 className="text-sm font-bold text-[#111827]">Recent Alerts</h3>
                <p className="text-[10px] text-[#9CA3AF] mt-0.5">Borrowers requiring attention</p>
              </div>
              <button
                onClick={() => navigate("/app/audit")}
                className="text-xs font-semibold text-[#7C8DFB] hover:text-[#4F46E5]"
              >
                View all
              </button>
            </div>

            {alerts.length > 0 ? (
              <div className="space-y-1">
                {alerts.slice(0, 3).map((a) => {
                  const borrower = borrowers.find((b) => b.id === a.borrower_id);
                  return (
                    <AlertCard
                      key={a.id}
                      title={a.title || a.message || "System Alert"}
                      borrowerName={borrower?.company_name || "Portfolio Company"}
                      timeAgo={new Date(a.created_at).toLocaleDateString()}
                      severity={a.severity?.toLowerCase() || "warning"}
                    />
                  );
                })}
              </div>
            ) : (
              <div className="py-8 text-center text-xs text-[#9CA3AF]">
                <p className="font-semibold text-[#111827]">No active alerts</p>
                <p className="text-[11px] text-[#6B7280] mt-0.5">Portfolio is in good standing.</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* ── THIRD ROW (Top Risky Borrowers + AI Insight) ─────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Top Risky Borrowers Grid (8 Cols) */}
        <div className="lg:col-span-8 bg-white rounded-2xl p-6 border border-[#EEF1F5] shadow-[0_4px_20px_rgba(17,24,39,0.04)]">
          <div className="flex items-center justify-between mb-5">
            <div>
              <h3 className="text-sm font-bold text-[#111827]">Top Risky Borrowers</h3>
              <p className="text-[10px] text-[#9CA3AF] mt-0.5">Sorted by highest risk score</p>
            </div>
            <button
              onClick={() => navigate("/app/borrowers")}
              className="text-xs font-semibold text-[#7C8DFB] hover:text-[#4F46E5] flex items-center gap-1"
            >
              <span>View all</span>
              <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>

          {borrowers.length > 0 ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {borrowers.slice(0, 4).map((b) => {
                const health = healthMap[b.id];
                return (
                  <BorrowerCard
                    key={b.id}
                    id={b.id}
                    name={b.company_name}
                    score={health?.score !== null && health?.score !== undefined ? health.score : 0}
                    category={health?.category || b.risk_rating?.level || "WATCH"}
                    onClick={() => navigate(`/app/borrowers?selected=${b.id}`)}
                  />
                );
              })}
            </div>
          ) : (
            <ImprovedEmptyState
              icon={Brain}
              title="No borrowers in portfolio"
              description="Add a borrower to start monitoring credit risk and covenant compliance."
              actionLabel="Add Borrower"
              onAction={() => navigate("/app/borrowers")}
            />
          )}
        </div>

        {/* Right: AI Insight Card (4 Cols) */}
        <div className="lg:col-span-4 flex">
          <InsightCard
            className="w-full h-full"
            insight={
              borrowers.length === 0
                ? "No borrowers registered yet. Add a borrower and upload credit agreements to begin automated risk intelligence."
                : highRiskCount > 0
                ? `${highRiskCount} high-risk borrower${highRiskCount > 1 ? "s" : ""} identified in your portfolio. Review covenant compliance and financial trends.`
                : "Portfolio is stable with 0 high-risk borrowers. Continue monitoring active covenants."
            }
            onAskCopilot={() => navigate("/app/copilot")}
          />
        </div>
      </div>
    </div>
  );
}
