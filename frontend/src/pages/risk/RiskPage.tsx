import { useState, useEffect } from "react";
import {
  ShieldCheck, Activity, TrendingUp, CheckCircle2,
  RefreshCw, FileText
} from "lucide-react";
import api from "@/lib/api";
import { useCompanyStore } from "@/store/company.store";

interface HealthData {
  score: number;
  category: string;
  explanation: string;
  breakdown: {
    financial_score: number;
    compliance_score: number;
    liquidity_score: number;
    leverage_score: number;
    trend_score: number;
  };
}

interface DefaultData {
  default_probability: number;
  risk_category: string;
  z_score: number;
  risk_factors: string[];
}

interface CovenantMonitoring {
  id: string;
  covenant_name: string;
  covenant_type: string;
  status: string;
  current_value: number;
  threshold_value: number;
  headroom_pct: number;
  reason: string;
}

interface Recommendation {
  id: string;
  priority: string;
  title: string;
  reasoning: string;
  action_required: boolean;
}

import { CreditMemoModal } from "@/components/reports/CreditMemoModal";

export default function RiskPage() {
  const { selectedCompanyId, selectedCompany } = useCompanyStore();
  const selectedBorrowerId = selectedCompanyId;
  const selectedBorrower = selectedCompany
    ? { company_name: selectedCompany.company_name, sector: selectedCompany.sector, country: selectedCompany.country }
    : null;

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
    setHealth(null); setDefaultPred(null); setCovenants([]); setRecommendations([]);
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

  return (
    <div className="space-y-8">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Borrower Risk & Covenant Intelligence</h1>
          <p className="text-muted-foreground mt-1">Multi-dimensional health scoring, covenant monitoring, and default prediction</p>
        </div>

        <div className="flex items-center gap-3">
          {selectedCompany && (
            <span className="text-sm text-muted-foreground bg-muted/40 border border-border px-3 py-1.5 rounded-lg">
              {selectedCompany.company_name} · {selectedCompany.sector}
            </span>
          )}
          <button
            onClick={() => setMemoModalOpen(true)}
            disabled={!selectedBorrowerId}
            className="flex items-center gap-2 px-4 py-2 bg-card border border-primary/30 text-primary text-sm font-semibold rounded-lg hover:bg-primary/10 transition-all disabled:opacity-50"
          >
            <FileText className="w-4 h-4" /> Export Credit Memo
          </button>
          <button
            onClick={handleRecalculate}
            disabled={refreshing || !selectedBorrowerId}
            className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground text-sm font-semibold rounded-lg hover:bg-primary/90 transition-all disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${refreshing ? "animate-spin" : ""}`} /> Recalculate Risk
          </button>
        </div>
      </div>

      {loading ? (
        <div className="py-20 text-center text-muted-foreground flex flex-col items-center">
          <Activity className="w-8 h-8 animate-spin text-primary mb-2" />
          <p className="font-semibold">Running Risk Intelligence Engine…</p>
        </div>
      ) : (
        <>
          {/* Top Metric Gauges */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Borrower Health Score Card */}
            <div className="bg-card border border-primary/20 p-6 rounded-2xl shadow-md relative overflow-hidden flex flex-col justify-between">
              <div>
                <div className="flex justify-between items-center mb-2">
                  <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Borrower Health Score</span>
                  <span className="px-2.5 py-0.5 text-xs font-bold rounded-full bg-emerald-400/10 text-emerald-400 border border-emerald-400/20 uppercase">
                    {health?.category ? health.category.toUpperCase() : "PENDING"}
                  </span>
                </div>
                <div className="flex items-baseline gap-2 mt-2">
                  <span className="text-5xl font-extrabold text-foreground">{health?.score ? health.score : "--"}</span>
                  <span className="text-muted-foreground font-semibold text-sm">/ 100</span>
                </div>
              </div>

              <div className="mt-4 pt-4 border-t border-border space-y-2 text-xs text-muted-foreground">
                <div className="flex justify-between">
                  <span>Financial Score</span>
                  <strong className="text-foreground">{health?.breakdown?.financial_score != null ? `${health.breakdown.financial_score}/100` : "--"}</strong>
                </div>
                <div className="flex justify-between">
                  <span>Compliance Score</span>
                  <strong className="text-foreground">{health?.breakdown?.compliance_score != null ? `${health.breakdown.compliance_score}/100` : "--"}</strong>
                </div>
                <div className="flex justify-between">
                  <span>Liquidity Score</span>
                  <strong className="text-foreground">{health?.breakdown?.liquidity_score != null ? `${health.breakdown.liquidity_score}/100` : "--"}</strong>
                </div>
              </div>
            </div>

            {/* Default Probability Card */}
            <div className="bg-card border border-border p-6 rounded-2xl shadow-sm flex flex-col justify-between">
              <div>
                <div className="flex justify-between items-center mb-2">
                  <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Default Probability</span>
                  <span className="px-2.5 py-0.5 text-xs font-bold rounded-full bg-blue-400/10 text-blue-400 border border-blue-400/20 uppercase">
                    {defaultPred?.risk_category ? defaultPred.risk_category.toUpperCase() : "PENDING"}
                  </span>
                </div>
                <div className="flex items-baseline gap-2 mt-2">
                  <span className="text-5xl font-extrabold text-foreground">{defaultPred?.default_probability != null ? `${defaultPred.default_probability}%` : "--"}</span>
                </div>
              </div>

              <div className="mt-4 pt-4 border-t border-border space-y-1.5 text-xs text-muted-foreground">
                <p className="font-semibold text-foreground">Top Risk Factors:</p>
                {defaultPred?.risk_factors && defaultPred.risk_factors.length > 0 ? (
                  defaultPred.risk_factors.slice(0, 2).map((rf, idx) => (
                    <p key={idx} className="flex items-start gap-1 text-muted-foreground">
                      <span className="text-primary">•</span> {rf}
                    </p>
                  ))
                ) : (
                  <p className="text-muted-foreground italic">No default risk factors identified.</p>
                )}
              </div>
            </div>

            {/* Entity Summary Card */}
            <div className="bg-card border border-border p-6 rounded-2xl shadow-sm flex flex-col justify-between">
              <div>
                <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Entity & Facility Context</span>
                <h3 className="text-xl font-bold mt-2 text-foreground">{selectedBorrower?.company_name}</h3>
                <p className="text-xs text-muted-foreground mt-0.5">{selectedBorrower?.sector} • {selectedBorrower?.country}</p>
              </div>

              <div className="mt-4 pt-4 border-t border-border space-y-2 text-xs text-muted-foreground">
                <div className="flex justify-between">
                  <span>Health Category</span>
                  <strong className="text-foreground">{health?.category ? health.category.toUpperCase() : "Pending Analysis"}</strong>
                </div>
                <div className="flex justify-between">
                  <span>Active Covenants</span>
                  <strong className="text-foreground">{covenants.length} Clauses</strong>
                </div>
                <div className="flex justify-between">
                  <span>AI Recommendations</span>
                  <strong className="text-foreground">{recommendations.length} Action Items</strong>
                </div>
              </div>
            </div>
          </div>

          {/* Covenant Compliance Table with Headroom & Reasoning */}
          <div className="space-y-4">
            <h3 className="text-xl font-bold flex items-center gap-2">
              <ShieldCheck className="w-5 h-5 text-primary" /> Active Covenant Compliance Monitoring
            </h3>

            {covenants.length === 0 ? (
              <div className="p-8 border border-dashed border-border rounded-2xl text-center text-muted-foreground">
                <FileText className="w-8 h-8 mx-auto mb-2 opacity-30" />
                <p className="font-semibold">No covenants monitored yet for this borrower</p>
              </div>
            ) : (
              <div className="bg-card border border-border rounded-2xl overflow-hidden shadow-sm">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-border bg-muted/40 text-xs font-semibold text-muted-foreground uppercase">
                      <th className="px-5 py-3 text-left">Covenant Name</th>
                      <th className="px-5 py-3 text-left">Type</th>
                      <th className="px-5 py-3 text-left">Current</th>
                      <th className="px-5 py-3 text-left">Threshold</th>
                      <th className="px-5 py-3 text-left">Headroom</th>
                      <th className="px-5 py-3 text-left">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {covenants.map((cov) => (
                      <tr key={cov.id} className="hover:bg-muted/20">
                        <td className="px-5 py-4 font-medium">
                          {cov.covenant_name}
                          <p className="text-xs text-muted-foreground font-normal mt-0.5 max-w-md">{cov.reason}</p>
                        </td>
                        <td className="px-5 py-4 capitalize text-xs text-muted-foreground">{cov.covenant_type}</td>
                        <td className="px-5 py-4 font-bold">{cov.current_value ? cov.current_value.toFixed(2) : "—"}</td>
                        <td className="px-5 py-4 font-semibold text-muted-foreground">{cov.threshold_value ? cov.threshold_value.toFixed(2) : "—"}</td>
                        <td className="px-5 py-4 font-semibold text-emerald-400">{cov.headroom_pct}%</td>
                        <td className="px-5 py-4">
                          <span className={`inline-flex items-center gap-1 text-xs font-bold px-2.5 py-0.5 rounded-full border uppercase ${
                            cov.status === "healthy"
                              ? "bg-emerald-400/10 text-emerald-400 border-emerald-400/20"
                              : "bg-amber-400/10 text-amber-400 border-amber-400/20"
                          }`}>
                            <CheckCircle2 className="w-3 h-3" /> {cov.status}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* AI Recommendations Section */}
          <div className="space-y-4">
            <h3 className="text-xl font-bold flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-primary" /> AI Risk Mitigation Recommendations
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {recommendations.map((rec) => (
                <div key={rec.id} className="bg-card border border-border p-5 rounded-2xl shadow-sm space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold uppercase tracking-wider text-primary">{rec.priority} Priority</span>
                    {rec.action_required && (
                      <span className="text-xs bg-amber-400/10 text-amber-400 border border-amber-400/20 px-2 py-0.5 rounded-full font-semibold">
                        Action Required
                      </span>
                    )}
                  </div>
                  <h4 className="font-bold text-foreground">{rec.title}</h4>
                  <p className="text-xs text-muted-foreground leading-relaxed">{rec.reasoning}</p>
                </div>
              ))}
            </div>
          </div>
        </>
      )}

      {/* Executive Credit Memo Printable Modal */}
      <CreditMemoModal
        borrowerId={selectedBorrowerId}
        isOpen={memoModalOpen}
        onClose={() => setMemoModalOpen(false)}
      />
    </div>
  );
}
