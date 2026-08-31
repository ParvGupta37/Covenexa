import { useState, useEffect } from "react";
import {
  Activity,
  ShieldCheck,
  TrendingUp,
  AlertTriangle,
  RefreshCw,
  FileText,
  Building2,
  AlertCircle,
  ClipboardList,
} from "lucide-react";
import {
  BarChart,
  Bar,
  XAxis,
  Tooltip,
  ResponsiveContainer
} from "recharts";

import api from "@/lib/api";
import { useCompanyStore } from "@/store/company.store";
import { KpiCard } from "@/components/shared/KpiCard";
import { StatusBadge } from "@/components/shared/StatusBadge";
import { EmptyState } from "@/components/shared/EmptyState";
import { CardSkeleton } from "@/components/shared/LoadingSkeleton";
import { CreditMemoModal } from "@/components/reports/CreditMemoModal";
import {
  SectionLabel,
  ImprovedEmptyState,
  CovenantStatusGuide,
} from "@/components/shared/Explainer";

interface HealthData {
  score: number | null;
  category: string;
  explanation: string;
  breakdown: {
    financial_score: number | null;
    compliance_score: number | null;
    liquidity_score: number | null;
    leverage_score: number | null;
    trend_score: number | null;
  };
}

interface DefaultData {
  default_probability: number | null;
  risk_category: string;
  z_score: number | null;
  risk_factors: string[];
}

interface CovenantMonitoring {
  id: string;
  covenant_name: string;
  covenant_type: string;
  status: string;
  current_value: number | null;
  threshold_value: number;
  headroom_pct: number | null;
  reason: string;
}

interface Recommendation {
  id: string;
  priority: string;
  title: string;
  reasoning: string;
  action_required: boolean;
}

export default function RiskPage() {
  const { selectedCompanyId, selectedCompany } = useCompanyStore();
  const selectedBorrowerId = selectedCompanyId;

  const [health, setHealth] = useState<HealthData | null>(null);
  const [defaultPred, setDefaultPred] = useState<DefaultData | null>(null);
  const [covenants, setCovenants] = useState<CovenantMonitoring[]>([]);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);

  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [memoModalOpen, setMemoModalOpen] = useState(false);

  useEffect(() => {
    if (!selectedBorrowerId) return;
    loadRiskData(selectedBorrowerId);
  }, [selectedBorrowerId]);

  async function loadRiskData(bId: string) {
    setLoading(true);
    setHealth(null);
    setDefaultPred(null);
    setCovenants([]);
    setRecommendations([]);
    try {
      const [hRes, dRes, cRes, rRes] = await Promise.all([
        api.get(`/api/v1/risk/health/${bId}`).catch(() => ({ data: null })),
        api.get(`/api/v1/risk/default/${bId}`).catch(() => ({ data: null })),
        api.get(`/api/v1/risk/covenants/${bId}`).catch(() => ({ data: [] })),
        api.get(`/api/v1/risk/recommendations/${bId}`).catch(() => ({ data: [] })),
      ]);

      if (hRes.data) setHealth(hRes.data);
      if (dRes.data) setDefaultPred(dRes.data);
      if (cRes.data) setCovenants(cRes.data);
      if (rRes.data) setRecommendations(rRes.data);
    } catch (e) {
      console.error("Failed to load risk data", e);
    } finally {
      setLoading(false);
    }
  }

  async function handleRecalculate() {
    if (!selectedBorrowerId) return;
    setRefreshing(true);
    try {
      await api.post(`/api/v1/risk/pipeline/${selectedBorrowerId}`);
      await loadRiskData(selectedBorrowerId);
    } catch (e) {
      console.error("Recalculation error", e);
    } finally {
      setRefreshing(false);
    }
  }

  const breakdownData = health?.breakdown
    ? [
        {
          name: "Financial",
          val: health.breakdown.financial_score ?? 0,
          rawVal: health.breakdown.financial_score,
          isAvailable: health.breakdown.financial_score !== null,
        },
        {
          name: "Compliance",
          val: health.breakdown.compliance_score ?? 0,
          rawVal: health.breakdown.compliance_score,
          isAvailable: health.breakdown.compliance_score !== null,
        },
        {
          name: "Liquidity",
          val: health.breakdown.liquidity_score ?? 0,
          rawVal: health.breakdown.liquidity_score,
          isAvailable: health.breakdown.liquidity_score !== null,
        },
        {
          name: "Leverage",
          val: health.breakdown.leverage_score ?? 0,
          rawVal: health.breakdown.leverage_score,
          isAvailable: health.breakdown.leverage_score !== null,
        },
        {
          name: "Trend",
          val: health.breakdown.trend_score ?? 0,
          rawVal: health.breakdown.trend_score,
          isAvailable: health.breakdown.trend_score !== null,
        },
      ]
    : [];

  return (
    <div className="space-y-8 pb-12">
      {/* ── Page Header ─────────────────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold text-[#111827] tracking-tight">
            Risk Monitor
          </h1>
          <p className="text-xs md:text-sm font-medium text-[#6B7280] mt-1">
            Borrower health, default probability, and covenant conditions for{" "}
            <strong className="text-[#111827]">
              {selectedCompany?.company_name || "Selected Borrower"}
            </strong>.
          </p>
        </div>

        <div className="flex items-center gap-3 shrink-0">
          <button
            onClick={handleRecalculate}
            disabled={refreshing || !selectedBorrowerId}
            className="flex items-center gap-2 px-4 py-2.5 bg-white border border-[#EEF1F5] hover:bg-gray-50 text-[#111827] font-semibold rounded-xl text-xs shadow-sm transition-all disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? "animate-spin" : ""}`} />
            <span>Recalculate</span>
          </button>

          <button
            onClick={() => setMemoModalOpen(true)}
            disabled={!selectedBorrowerId}
            className="flex items-center gap-2 px-4 py-2.5 bg-[#7C8DFB] hover:bg-[#6366F1] text-white font-semibold rounded-xl text-xs shadow-sm transition-all disabled:opacity-50"
          >
            <FileText className="w-3.5 h-3.5" />
            <span>Credit Memo</span>
          </button>
        </div>
      </div>

      {/* ── Top Metric Cards ────────────────────────────────────────── */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <KpiCard
          title="Health Score"
          subtitle="Overall borrower financial health."
          tooltip="Composite score (0–100) measuring the borrower's financial condition using financial ratios, compliance status, liquidity, leverage, and trend signals. Higher is better."
          value={
            health?.score !== null && health?.score !== undefined
              ? `${health.score.toFixed(1)} / 100`
              : "N/A"
          }
          badgeText={health?.category || "UNANALYZED"}
          badgeType={
            health?.category?.toUpperCase().includes("HIGH")
              ? "danger"
              : health?.category?.toUpperCase().includes("WATCH")
              ? "watch"
              : "success"
          }
          icon={Activity}
          iconBgColor="#E8ECFF"
          iconColor="#4F46E5"
        />

        <KpiCard
          title="Default Probability"
          subtitle="Estimated likelihood of default."
          tooltip="Analytical estimate of the probability the borrower may default, based on current financial signals. This is a model estimate — not a guaranteed prediction. Higher % = greater risk."
          value={
            defaultPred?.default_probability !== null && defaultPred?.default_probability !== undefined
              ? `${defaultPred.default_probability.toFixed(1)}%`
              : "N/A"
          }
          badgeText={defaultPred?.risk_category || "NO DATA"}
          badgeType={
            defaultPred?.risk_category?.toUpperCase().includes("HIGH")
              ? "danger"
              : "warning"
          }
          icon={AlertTriangle}
          iconBgColor="#FEE2E2"
          iconColor="#EF4444"
        />

        <KpiCard
          title="Altman Z-Score"
          subtitle="Bankruptcy distress indicator."
          tooltip="A widely-used academic model predicting financial distress. Safe zone: above 2.99. Grey zone: 1.81–2.99. Distress zone: below 1.81. N/A means insufficient financial data."
          value={
            defaultPred?.z_score !== null && defaultPred?.z_score !== undefined
              ? defaultPred.z_score.toFixed(2)
              : "N/A"
          }
          trendText="Safe zone > 2.99"
          trendUp={false}
          icon={TrendingUp}
          iconBgColor="#FEF3C7"
          iconColor="#D97706"
        />

        <KpiCard
          title="Monitored Covenants"
          subtitle="Active financial conditions from agreements."
          tooltip="Covenants are contractual requirements in credit agreements (e.g., keep leverage below 4x). This shows how many are actively tracked and how many are currently breached."
          value={covenants.length}
          badgeText={`${covenants.filter((c) => ["breach", "critical"].includes(c.status)).length} Breached`}
          badgeType="danger"
          icon={ShieldCheck}
          iconBgColor="#D1FAE5"
          iconColor="#10B981"
        />
      </div>

      {/* ── Risk Factor Breakdown & Covenants Grid ───────────────────── */}
      {loading ? (
        <div className="space-y-4">
          <CardSkeleton />
          <CardSkeleton />
        </div>
      ) : !selectedBorrowerId ? (
        <EmptyState
          icon={Building2}
          title="No Borrower Selected"
          description="Select a borrower company from the header dropdown to view risk analytics."
        />
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left Column: Breakdown Chart & Risk Drivers (7 Cols) */}
          <div className="lg:col-span-7 space-y-6">
            {/* Component Breakdown Bar Chart */}
            <div className="bg-white rounded-2xl p-6 border border-[#EEF1F5] shadow-[0_4px_20px_rgba(17,24,39,0.04)]">
              <SectionLabel
                tooltip="Each bar shows a sub-score contributing to the overall Health Score. Financial = profitability ratios. Compliance = covenant adherence. Liquidity = short-term cash. Leverage = debt load. Trend = recent trajectory."
                className="text-sm font-bold text-[#111827]"
              >
                Health Score Breakdown
              </SectionLabel>
              <p className="text-xs text-[#6B7280] mt-1 mb-4">
                Five contributing factors, each scored 0–100. Missing factors are omitted from weighted scoring.
              </p>

              {breakdownData.length > 0 ? (
                <div className="space-y-4">
                  <div className="h-52 w-full">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={breakdownData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                        <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fontSize: 11, fill: "#9CA3AF" }} />
                        <Tooltip
                          cursor={{ fill: "#F3F4FF" }}
                          content={({ active, payload }) => {
                            if (active && payload && payload.length) {
                              const data = payload[0].payload;
                              return (
                                <div className="bg-[#111827] text-white p-2.5 rounded-xl text-xs shadow-lg space-y-0.5 border border-gray-700">
                                  <p className="font-bold text-gray-200">{data.name}</p>
                                  <p className="text-gray-400">
                                    Score:{" "}
                                    <span className="font-semibold text-white">
                                      {data.isAvailable ? `${data.val.toFixed(1)} / 100` : "N/A (Unavailable)"}
                                    </span>
                                  </p>
                                </div>
                              );
                            }
                            return null;
                          }}
                        />
                        <Bar dataKey="val" fill="#7C8DFB" radius={[8, 8, 0, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>

                  {/* Component badges */}
                  <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 pt-2 border-t border-[#EEF1F5] text-[11px]">
                    {breakdownData.map((b) => (
                      <div key={b.name} className="p-2 rounded-xl bg-[#F8F9FC] border border-[#EEF1F5] text-center">
                        <p className="text-[#6B7280] text-[10px]">{b.name}</p>
                        <p className="font-bold text-[#111827] mt-0.5">
                          {b.isAvailable ? `${b.val.toFixed(1)}` : "N/A"}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <ImprovedEmptyState
                  icon={Activity}
                  title="No analysis available"
                  description="This borrower has not been analyzed yet. Click Recalculate to generate health and risk indicators."
                />
              )}
            </div>

            {/* Key Risk Factors List with Explicit Analyst Labels */}
            <div className="bg-white rounded-2xl p-6 border border-[#EEF1F5] shadow-[0_4px_20px_rgba(17,24,39,0.04)] space-y-4">
              <div>
                <SectionLabel
                  tooltip="Key factors identified by the risk model that are negatively affecting this borrower's credit quality."
                  className="text-sm font-bold text-[#111827]"
                >
                  Key Risk Drivers
                </SectionLabel>
                <p className="text-xs text-[#6B7280] mt-1">
                  Signals currently impacting credit quality.
                </p>
              </div>

              {defaultPred?.risk_factors && defaultPred.risk_factors.length > 0 ? (
                <div className="space-y-3">
                  {defaultPred.risk_factors.map((rf, idx) => (
                    <div key={idx} className="p-3.5 rounded-xl bg-[#F8F9FC] border border-[#EEF1F5] space-y-1.5">
                      <div className="flex items-center gap-2">
                        <span className="text-[9px] font-bold uppercase tracking-wider text-[#EF4444] bg-[#FEE2E2] px-2 py-0.5 rounded-full">
                          RISK SIGNAL
                        </span>
                        <span className="text-[10px] text-[#9CA3AF] font-mono">#{idx + 1}</span>
                      </div>
                      <p className="text-xs font-semibold text-[#111827]">{rf}</p>
                      <p className="text-[11px] text-[#6B7280] border-t border-[#EEF1F5] pt-1.5 leading-relaxed">
                        <strong className="text-[#111827]">WHY IT MATTERS:</strong> May restrict liquidity or trigger credit re-rating if unaddressed.
                      </p>
                    </div>
                  ))}
                </div>
              ) : (
                <ImprovedEmptyState
                  icon={AlertCircle}
                  title="No risk drivers reported"
                  description="Run an analysis to identify specific financial signals impacting this borrower."
                />
              )}
            </div>
          </div>

          {/* Right Column: Covenants & AI Recommendations (5 Cols) */}
          <div className="lg:col-span-5 space-y-6">
            {/* Covenant Compliance Status */}
            <div className="bg-white rounded-2xl p-6 border border-[#EEF1F5] shadow-[0_4px_20px_rgba(17,24,39,0.04)] space-y-3">
              <div>
                <SectionLabel
                  tooltip="A covenant is a financial condition in the credit agreement that the borrower must continuously satisfy. Breaches can signal increasing credit risk."
                  className="text-sm font-bold text-[#111827]"
                >
                  Covenant Status
                </SectionLabel>
                <p className="text-xs text-[#6B7280] mt-1">
                  Financial conditions from the credit agreement.
                </p>
              </div>

              {/* Status Guide */}
              <CovenantStatusGuide />

              {covenants.length > 0 ? (
                <div className="space-y-3">
                  {covenants.map((cov) => (
                    <div key={cov.id} className="p-3.5 rounded-xl border border-[#EEF1F5] bg-[#F8F9FC] space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-xs text-[#111827]">{cov.covenant_name}</span>
                        <StatusBadge status={cov.status} />
                      </div>
                      <div className="flex justify-between text-[11px] text-[#6B7280]">
                        <span>
                          Current:{" "}
                          <strong className="text-[#111827]">
                            {cov.current_value !== null ? `${cov.current_value}x` : "N/A"}
                          </strong>
                        </span>
                        <span>
                          Threshold:{" "}
                          <strong className="text-[#111827]">
                            {cov.threshold_value !== null ? `${cov.threshold_value}x` : "N/A"}
                          </strong>
                        </span>
                      </div>
                      <p className="text-[10px] text-[#6B7280] bg-white px-2 py-1 rounded-lg border border-[#EEF1F5] flex items-center justify-between">
                        <span className="font-bold text-[#111827]">EVIDENCE / HEADROOM:</span>
                        <span>
                          {cov.headroom_pct !== null
                            ? `${cov.headroom_pct.toFixed(1)}% buffer remaining`
                            : "N/A (Ratio unavailable)"}
                        </span>
                      </p>
                    </div>
                  ))}
                </div>
              ) : (
                <ImprovedEmptyState
                  icon={ClipboardList}
                  title="No covenants monitored"
                  description="No covenants are currently tracked for this facility. Upload a credit agreement to extract covenant terms."
                />
              )}
            </div>

            {/* AI Action Recommendations with Explicit Analyst Labels */}
            <div className="bg-white rounded-2xl p-6 border border-[#EEF1F5] shadow-[0_4px_20px_rgba(17,24,39,0.04)] space-y-3">
              <div>
                <SectionLabel
                  tooltip="AI-generated action suggestions based on the borrower's current risk picture, covenant status, and financial trajectory. These are recommendations — analyst judgment is required before acting."
                  className="text-sm font-bold text-[#111827]"
                >
                  AI Recommendations
                </SectionLabel>
                <p className="text-xs text-[#6B7280] mt-1">
                  Suggested actions based on current risk analysis.
                </p>
              </div>

              {recommendations.length > 0 ? (
                <div className="space-y-3">
                  {recommendations.map((rec) => (
                    <div key={rec.id} className="p-3.5 rounded-xl border border-[#EEF1F5] bg-[#F8F9FC] space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-xs text-[#111827]">{rec.title}</span>
                        <span className="text-[9px] font-bold uppercase tracking-wider text-[#7C8DFB] bg-[#E8ECFF] px-2 py-0.5 rounded-full">
                          {rec.priority}
                        </span>
                      </div>
                      <p className="text-xs text-[#6B7280] leading-relaxed">{rec.reasoning}</p>
                      <div className="pt-1.5 border-t border-[#EEF1F5] flex items-center justify-between text-[10px]">
                        <span className="font-bold text-[#4F46E5] uppercase tracking-wide">
                          RECOMMENDED ACTION
                        </span>
                        <span className="text-[#6B7280]">Analyst Review Required</span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <ImprovedEmptyState
                  icon={AlertTriangle}
                  title="No recommendations yet"
                  description="Run a risk analysis to generate AI-powered credit action recommendations."
                />
              )}
            </div>
          </div>
        </div>
      )}

      {selectedBorrowerId && (
        <CreditMemoModal
          isOpen={memoModalOpen}
          onClose={() => setMemoModalOpen(false)}
          borrowerId={selectedBorrowerId}
        />
      )}
    </div>
  );
}
