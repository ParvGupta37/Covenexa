import { useState, useEffect } from "react";
import {
  X,
  Printer,
  FileText,
  AlertTriangle,
  Loader2,
  Sparkles,
  Database,
  Search,
  Network,
} from "lucide-react";
import api from "@/lib/api";

interface CreditMemoModalProps {
  borrowerId: string;
  isOpen: boolean;
  onClose: () => void;
}

export function CreditMemoModal({ borrowerId, isOpen, onClose }: CreditMemoModalProps) {
  const [memo, setMemo] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!isOpen || !borrowerId) return;
    fetchMemo();
  }, [isOpen, borrowerId]);

  async function fetchMemo() {
    setLoading(true);
    try {
      const res = await api.get(`/api/v1/reports/credit-memo/${borrowerId}`);
      setMemo(res.data);
    } catch (e) {
      console.error("Failed to load credit memo", e);
    } finally {
      setLoading(false);
    }
  }

  if (!isOpen) return null;

  const handlePrint = () => {
    window.print();
  };

  // Safe metric formatters respecting None != 0 (N/A for missing metrics)
  const formatCurrency = (val: number | null | undefined, currency = "USD") => {
    if (val === null || val === undefined) return "N/A";
    const absVal = Math.abs(val);
    const symbol = currency === "USD" ? "$" : `${currency} `;
    if (absVal >= 1e9) return `${symbol}${(val / 1e9).toFixed(2)}B`;
    if (absVal >= 1e6) return `${symbol}${(val / 1e6).toFixed(2)}M`;
    if (absVal >= 1e3) return `${symbol}${(val / 1e3).toFixed(1)}K`;
    return `${symbol}${val.toLocaleString()}`;
  };

  const formatRatio = (val: number | null | undefined, suffix = "x") => {
    if (val === null || val === undefined) return "N/A";
    return `${val.toFixed(2)}${suffix}`;
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-md p-4 overflow-y-auto">
      <div className="bg-white border border-[#EEF1F5] w-full max-w-4xl rounded-2xl shadow-2xl overflow-hidden my-8 animate-in fade-in zoom-in duration-200 text-[#111827]">
        {/* Modal Toolbar (hidden when printing) */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-[#EEF1F5] bg-[#F8F9FC] print:hidden">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-[#E8ECFF] text-[#4F46E5] rounded-xl border border-[#C7D2FE]">
              <FileText className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-[#111827]">Executive Credit Memorandum</h2>
              <p className="text-xs text-[#6B7280]">
                Summarizes borrower financial health, risk assessment, supporting evidence, and recommended actions. Missing data is rendered as N/A.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={handlePrint}
              disabled={loading || !memo}
              className="flex items-center gap-2 px-4 py-2 bg-[#7C8DFB] text-white font-semibold rounded-xl text-xs hover:bg-[#6366F1] transition-all disabled:opacity-50 shadow-sm"
            >
              <Printer className="w-4 h-4" /> Export / Print PDF
            </button>
            <button
              onClick={onClose}
              className="p-2 text-[#6B7280] hover:text-[#111827] rounded-lg hover:bg-gray-100 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Report Printable Document Canvas */}
        <div className="p-8 md:p-12 space-y-8 print:p-0 print:m-0 print:bg-white print:text-black">
          {loading ? (
            <div className="py-20 text-center text-[#6B7280] flex flex-col items-center">
              <Loader2 className="w-8 h-8 animate-spin text-[#7C8DFB] mb-2" />
              <p className="font-semibold text-sm">Synthesizing Credit Memorandum Report...</p>
            </div>
          ) : !memo ? (
            <div className="py-16 text-center text-[#6B7280]">
              <AlertTriangle className="w-8 h-8 mx-auto mb-2 text-[#F97316]" />
              <p className="font-semibold text-sm">Failed to generate credit memo for this borrower.</p>
              <p className="text-xs text-[#9CA3AF] mt-1">Please try again or run a risk analysis pipeline first.</p>
            </div>
          ) : (
            <div className="space-y-8">
              {/* Document Header */}
              <div className="border-b-2 border-[#7C8DFB]/30 pb-6 flex justify-between items-start gap-4">
                <div>
                  <div className="flex items-center gap-2 text-xs font-bold text-[#4F46E5] tracking-widest uppercase mb-1">
                    <Sparkles className="w-3.5 h-3.5" /> Confidential Credit Risk Memorandum
                  </div>
                  <h1 className="text-3xl font-extrabold text-[#111827]">{memo.title}</h1>
                  <p className="text-xs text-[#6B7280] mt-1">
                    Borrower: <strong className="text-[#111827]">{memo.borrower.company_name}</strong> · Sector: <strong className="text-[#111827]">{memo.borrower.sector}</strong> ({memo.borrower.country})
                  </p>
                </div>

                <div className="text-right border-l border-[#EEF1F5] pl-6">
                  <span className="text-[10px] uppercase font-bold text-[#6B7280] tracking-wider block">Generated Date</span>
                  <span className="text-xs font-semibold text-[#111827]">{new Date().toLocaleDateString("en-US", { month: "long", day: "numeric", year: "numeric" })}</span>
                </div>
              </div>

              {/* 1. EXECUTIVE SUMMARY */}
              <div className="bg-[#F8F9FC] border border-[#EEF1F5] p-6 rounded-2xl space-y-4">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#EEF1F5] pb-4">
                  <div>
                    <span className="text-[10px] font-bold text-[#7C8DFB] bg-[#E8ECFF] px-2.5 py-0.5 rounded-full uppercase tracking-wider">
                      AI Generated Analysis
                    </span>
                    <h3 className="text-xl font-black text-[#111827] mt-1.5">{memo.summary.recommendation}</h3>
                  </div>

                  <div className="flex items-center gap-6">
                    <div className="text-center">
                      <span className="text-[10px] text-[#6B7280] uppercase font-bold block">Health Score</span>
                      <p className="text-2xl font-extrabold text-[#111827]">
                        {memo.summary.health_score !== null ? `${memo.summary.health_score.toFixed(1)} / 100` : "N/A"}
                      </p>
                    </div>
                    <div className="text-center border-l border-[#EEF1F5] pl-6">
                      <span className="text-[10px] text-[#6B7280] uppercase font-bold block">Default Prob</span>
                      <p className="text-2xl font-extrabold text-[#111827]">
                        {memo.summary.default_probability !== null ? `${memo.summary.default_probability.toFixed(1)}%` : "N/A"}
                      </p>
                    </div>
                  </div>
                </div>

                <p className="text-xs leading-relaxed text-[#4B5563] font-medium">
                  {memo.summary.recommendation_reason}
                </p>
              </div>

              {/* 2. BORROWER & FACILITY OVERVIEW */}
              <div className="space-y-4">
                <h4 className="font-bold text-sm text-[#111827] border-b border-[#EEF1F5] pb-2 flex items-center justify-between">
                  <span>1. Borrower & Facility Overview</span>
                  <span className="text-[10px] text-[#6B7280] font-normal uppercase">Source: Verified Database Records</span>
                </h4>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs">
                  <div className="p-3 bg-[#F8F9FC] border border-[#EEF1F5] rounded-xl">
                    <span className="text-[11px] text-[#6B7280] font-semibold block">Entity Name</span>
                    <span className="text-xs font-bold text-[#111827] mt-0.5 block truncate">{memo.borrower.company_name}</span>
                  </div>
                  <div className="p-3 bg-[#F8F9FC] border border-[#EEF1F5] rounded-xl">
                    <span className="text-[11px] text-[#6B7280] font-semibold block">Sector</span>
                    <span className="text-xs font-bold text-[#111827] mt-0.5 block">{memo.borrower.sector}</span>
                  </div>
                  <div className="p-3 bg-[#F8F9FC] border border-[#EEF1F5] rounded-xl">
                    <span className="text-[11px] text-[#6B7280] font-semibold block">Country</span>
                    <span className="text-xs font-bold text-[#111827] mt-0.5 block">{memo.borrower.country}</span>
                  </div>
                  <div className="p-3 bg-[#F8F9FC] border border-[#EEF1F5] rounded-xl">
                    <span className="text-[11px] text-[#6B7280] font-semibold block">Active Facilities</span>
                    <span className="text-xs font-bold text-[#111827] mt-0.5 block">
                      {memo.facilities ? `${memo.facilities.length} facility` : "0 facilities"}
                    </span>
                  </div>
                </div>
              </div>

              {/* 3. FINANCIAL POSITION */}
              <div className="space-y-4">
                <h4 className="font-bold text-sm text-[#111827] border-b border-[#EEF1F5] pb-2 flex items-center justify-between">
                  <span>2. Financial Position & Metrics</span>
                  <span className="text-[10px] text-[#6B7280] font-normal uppercase">Source: Financial Statements</span>
                </h4>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs">
                  <div className="p-3 bg-[#F8F9FC] border border-[#EEF1F5] rounded-xl">
                    <span className="text-[11px] text-[#6B7280] font-semibold block">Revenue</span>
                    <span className="text-sm font-bold text-[#111827] mt-0.5 block">
                      {formatCurrency(memo.financial_highlights.revenue, memo.financial_highlights.currency)}
                    </span>
                  </div>
                  <div className="p-3 bg-[#F8F9FC] border border-[#EEF1F5] rounded-xl">
                    <span className="text-[11px] text-[#6B7280] font-semibold block">EBITDA</span>
                    <span className="text-sm font-bold text-[#111827] mt-0.5 block">
                      {formatCurrency(memo.financial_highlights.ebitda, memo.financial_highlights.currency)}
                    </span>
                  </div>
                  <div className="p-3 bg-[#F8F9FC] border border-[#EEF1F5] rounded-xl">
                    <span className="text-[11px] text-[#6B7280] font-semibold block">Total Debt</span>
                    <span className="text-sm font-bold text-[#111827] mt-0.5 block">
                      {formatCurrency(memo.financial_highlights.total_debt, memo.financial_highlights.currency)}
                    </span>
                  </div>
                  <div className="p-3 bg-[#F8F9FC] border border-[#EEF1F5] rounded-xl">
                    <span className="text-[11px] text-[#6B7280] font-semibold block">Cash Reserve</span>
                    <span className="text-sm font-bold text-[#111827] mt-0.5 block">
                      {formatCurrency(memo.financial_highlights.cash, memo.financial_highlights.currency)}
                    </span>
                  </div>
                  <div className="p-3 bg-[#F8F9FC] border border-[#EEF1F5] rounded-xl">
                    <span className="text-[11px] text-[#6B7280] font-semibold block">Leverage Ratio (Debt/EBITDA)</span>
                    <span className="text-sm font-bold text-[#111827] mt-0.5 block">
                      {formatRatio(memo.financial_highlights.leverage_ratio)}
                    </span>
                  </div>
                  <div className="p-3 bg-[#F8F9FC] border border-[#EEF1F5] rounded-xl">
                    <span className="text-[11px] text-[#6B7280] font-semibold block">Interest Coverage</span>
                    <span className="text-sm font-bold text-[#111827] mt-0.5 block">
                      {formatRatio(memo.financial_highlights.interest_coverage)}
                    </span>
                  </div>
                  <div className="p-3 bg-[#F8F9FC] border border-[#EEF1F5] rounded-xl">
                    <span className="text-[11px] text-[#6B7280] font-semibold block">Net Income</span>
                    <span className="text-sm font-bold text-[#111827] mt-0.5 block">
                      {formatCurrency(memo.financial_highlights.net_income, memo.financial_highlights.currency)}
                    </span>
                  </div>
                  <div className="p-3 bg-[#F8F9FC] border border-[#EEF1F5] rounded-xl">
                    <span className="text-[11px] text-[#6B7280] font-semibold block">Risk Rating</span>
                    <span className="text-sm font-bold text-[#111827] mt-0.5 block">
                      {memo.summary.default_risk_category}
                    </span>
                  </div>
                </div>
              </div>

              {/* 4. COVENANT MONITORING */}
              <div className="space-y-4">
                <h4 className="font-bold text-sm text-[#111827] border-b border-[#EEF1F5] pb-2 flex items-center justify-between">
                  <span>3. Covenant Compliance & Thresholds</span>
                  <span className="text-[10px] text-[#6B7280] font-normal uppercase">Source: Extracted Agreement Terms</span>
                </h4>
                {memo.covenant_summary.all_covenants.length === 0 ? (
                  <p className="text-xs text-[#9CA3AF]">No covenants registered under active facility.</p>
                ) : (
                  <div className="overflow-x-auto border border-[#EEF1F5] rounded-xl">
                    <table className="w-full text-left text-xs">
                      <thead>
                        <tr className="bg-[#F8F9FC] border-b border-[#EEF1F5] font-semibold text-[#6B7280]">
                          <th className="p-3">Covenant Name</th>
                          <th className="p-3">Type</th>
                          <th className="p-3">Status</th>
                          <th className="p-3">Threshold</th>
                          <th className="p-3">Current</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[#EEF1F5]">
                        {memo.covenant_summary.all_covenants.map((c: any) => (
                          <tr key={c.id}>
                            <td className="p-3 font-semibold text-[#111827]">{c.covenant_name}</td>
                            <td className="p-3 capitalize text-[#6B7280]">{c.covenant_type}</td>
                            <td className="p-3">
                              <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase ${
                                ["breach", "critical"].includes(c.status)
                                  ? "bg-[#FEE2E2] text-[#EF4444]"
                                  : c.status === "warning"
                                  ? "bg-[#FFEDD5] text-[#F97316]"
                                  : "bg-[#D1FAE5] text-[#10B981]"
                              }`}>
                                {c.status}
                              </span>
                            </td>
                            <td className="p-3 font-mono text-[#111827]">{c.threshold_value}x</td>
                            <td className="p-3 font-mono text-[#111827]">
                              {c.current_value !== null ? `${c.current_value}x` : "N/A"}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>

              {/* 5. PRIMARY RISK FACTORS & STRESS */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-3">
                  <h4 className="font-bold text-sm text-[#111827] border-b border-[#EEF1F5] pb-2">
                    4. Primary Risk Factors
                  </h4>
                  <ul className="space-y-2 text-xs text-[#4B5563]">
                    {memo.risk_factors.map((factor: string, idx: number) => (
                      <li key={idx} className="flex items-start gap-2 bg-[#F8F9FC] p-2.5 rounded-xl border border-[#EEF1F5]">
                        <AlertTriangle className="w-3.5 h-3.5 text-[#F97316] shrink-0 mt-0.5" />
                        <span>{factor}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                <div className="space-y-3">
                  <h4 className="font-bold text-sm text-[#111827] border-b border-[#EEF1F5] pb-2">
                    5. Stress Simulation Observations
                  </h4>
                  {memo.stress_observations ? (
                    <div className="p-3.5 bg-[#F8F9FC] border border-[#EEF1F5] rounded-xl space-y-2 text-xs">
                      <p className="font-bold text-[#111827]">
                        Scenario: {memo.stress_observations.scenario_name || "Adverse Shock"}
                      </p>
                      <p className="text-[#6B7280]">
                        Projected Health Score: <strong className="text-[#111827]">{memo.stress_observations.projected_health_score ?? "N/A"}</strong>
                      </p>
                      <p className="text-[#6B7280]">
                        Projected Default Prob: <strong className="text-[#111827]">{memo.stress_observations.projected_default_prob != null ? `${memo.stress_observations.projected_default_prob}%` : "N/A"}</strong>
                      </p>
                      <p className={memo.stress_observations.at_risk ? "text-[#EF4444] font-semibold" : "text-[#10B981] font-semibold"}>
                        {memo.stress_observations.at_risk ? "Facility at risk under stress scenario." : "Facility resilient under stress scenario."}
                      </p>
                    </div>
                  ) : (
                    <p className="text-xs text-[#9CA3AF]">
                      No stress simulation executed for this borrower yet. Run a scenario in Stress Testing to generate projections.
                    </p>
                  )}
                </div>
              </div>

              {/* 6. EVIDENCE & GROUNDING SOURCES */}
              <div className="space-y-3 pt-4 border-t border-[#EEF1F5]">
                <h4 className="font-bold text-xs uppercase tracking-wider text-[#6B7280]">
                  6. Evidence & Grounding Sources
                </h4>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
                  {memo.evidence_sources?.map((src: any, i: number) => (
                    <div key={i} className="p-3 bg-[#F8F9FC] border border-[#EEF1F5] rounded-xl space-y-1">
                      <div className="flex items-center gap-1.5 font-bold text-[#111827]">
                        {src.type === "Financial Data" ? (
                          <Database className="w-3.5 h-3.5 text-[#10B981]" />
                        ) : src.type === "Extracted Document" ? (
                          <Search className="w-3.5 h-3.5 text-[#7C8DFB]" />
                        ) : (
                          <Network className="w-3.5 h-3.5 text-[#F97316]" />
                        )}
                        <span>{src.type}</span>
                      </div>
                      <p className="text-[11px] text-[#6B7280] leading-relaxed">{src.description}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
