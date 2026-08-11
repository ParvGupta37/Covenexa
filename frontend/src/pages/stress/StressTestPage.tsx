import { useState, useEffect } from "react";
import { Sliders, Play, AlertTriangle, ShieldCheck, BarChart2, RefreshCw, Info } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend, Cell } from "recharts";
import api from "@/lib/api";
import { useCompanyStore } from "@/store/company.store";

// ── Types ─────────────────────────────────────────────────────────────────────
interface StressResult {
  projected_health_score: number | null;
  projected_default_prob: number | null;
  covenant_breaches_count: number;
  at_risk: boolean | null;
  calculation_status: "valid" | "partial_data" | "insufficient_data";
  data_quality: {
    ebitda_available: boolean;
    revenue_available: boolean;
    debt_available: boolean;
    interest_available: boolean;
    leverage_calculable: boolean;
    coverage_calculable: boolean;
  };
  caveats: string[];
  details: {
    baseline: { leverage: number | null; coverage: number | null };
    stressed: {
      revenue: number;
      ebitda: number | null;
      debt: number;
      leverage: number | null;
      coverage: number | null;
    };
  };
}

// ── Helpers ───────────────────────────────────────────────────────────────────
/** Display a financial ratio or "N/A" — never silently converts null → 0. */
function fmtRatio(val: number | null | undefined): string {
  if (val == null) return "N/A";
  return `${val.toFixed(2)}x`;
}

const STATUS_LABELS: Record<string, string> = {
  valid: "Full Calculation",
  partial_data: "Partial Data",
  insufficient_data: "Insufficient Data",
};

const STATUS_COLORS: Record<string, string> = {
  valid: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
  partial_data: "bg-amber-500/10 text-amber-400 border-amber-500/20",
  insufficient_data: "bg-red-500/10 text-red-400 border-red-500/20",
};

export default function StressTestPage() {
  const { selectedCompanyId, selectedCompany } = useCompanyStore();
  const selectedBorrowerId = selectedCompanyId;

  const [revenueChange, setRevenueChange] = useState<number>(-15);
  const [ebitdaChange, setEbitdaChange] = useState<number>(-20);
  const [rateChangeBps, setRateChangeBps] = useState<number>(200);
  const [debtChange, setDebtChange] = useState<number>(10);

  const [result, setResult] = useState<StressResult | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!selectedBorrowerId) return;
    runSimulation();
  }, [selectedBorrowerId]);

  async function runSimulation() {
    if (!selectedBorrowerId) return;
    setLoading(true);
    try {
      const res = await api.post("/api/v1/risk/stress", {
        borrower_id: selectedBorrowerId,
        scenario_name: "Interactive Stress Simulation",
        revenue_change_pct: revenueChange,
        ebitda_change_pct: ebitdaChange,
        interest_rate_change_bps: rateChangeBps,
        debt_change_pct: debtChange,
      });
      setResult(res.data);
    } catch (e) {
      console.error("Stress simulation error", e);
    } finally {
      setLoading(false);
    }
  }

  // Chart: only include bars where both values are available numbers.
  // null → omit from chart rather than display as "0".
  const chartData = [
    {
      metric: "Leverage (x)",
      Baseline: result?.details?.baseline?.leverage ?? null,
      Stressed: result?.details?.stressed?.leverage ?? null,
      baselineAvailable: result?.details?.baseline?.leverage != null,
      stressedAvailable: result?.details?.stressed?.leverage != null,
    },
    {
      metric: "Coverage (x)",
      Baseline: result?.details?.baseline?.coverage ?? null,
      Stressed: result?.details?.stressed?.coverage ?? null,
      baselineAvailable: result?.details?.baseline?.coverage != null,
      stressedAvailable: result?.details?.stressed?.coverage != null,
    },
  ];

  const calcStatus = result?.calculation_status ?? "valid";
  const isInsufficient = calcStatus === "insufficient_data";

  return (
    <div className="space-y-8">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Portfolio & Borrower Stress Testing</h1>
          <p className="text-muted-foreground mt-1">Simulate macroeconomic shocks, rate hikes, and EBITDA contraction</p>
        </div>

        {selectedCompany && (
          <span className="text-sm font-semibold text-foreground bg-card border border-border px-4 py-2 rounded-lg">
            Entity: <span className="text-primary">{selectedCompany.company_name}</span> ({selectedCompany.sector})
          </span>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Sliders Control Panel */}
        <div className="bg-card border border-border p-6 rounded-2xl shadow-sm space-y-6">
          <div className="flex items-center gap-2 font-bold text-base border-b border-border pb-3">
            <Sliders className="w-4 h-4 text-primary" /> Scenario Sliders
          </div>

          <div className="space-y-2">
            <div className="flex justify-between text-xs font-semibold">
              <span>Revenue Change</span>
              <span className={revenueChange < 0 ? "text-red-400" : "text-emerald-400"}>{revenueChange}%</span>
            </div>
            <input
              type="range" min="-50" max="20" value={revenueChange}
              onChange={(e) => setRevenueChange(Number(e.target.value))}
              className="w-full accent-primary cursor-pointer"
            />
          </div>

          <div className="space-y-2">
            <div className="flex justify-between text-xs font-semibold">
              <span>EBITDA Change</span>
              <span className={ebitdaChange < 0 ? "text-red-400" : "text-emerald-400"}>{ebitdaChange}%</span>
            </div>
            <input
              type="range" min="-50" max="20" value={ebitdaChange}
              onChange={(e) => setEbitdaChange(Number(e.target.value))}
              className="w-full accent-primary cursor-pointer"
            />
          </div>

          <div className="space-y-2">
            <div className="flex justify-between text-xs font-semibold">
              <span>Interest Rate Delta</span>
              <span className="text-amber-400">+{rateChangeBps} bps</span>
            </div>
            <input
              type="range" min="0" max="600" step="50" value={rateChangeBps}
              onChange={(e) => setRateChangeBps(Number(e.target.value))}
              className="w-full accent-primary cursor-pointer"
            />
          </div>

          <div className="space-y-2">
            <div className="flex justify-between text-xs font-semibold">
              <span>Debt Load Expansion</span>
              <span className="text-blue-400">+{debtChange}%</span>
            </div>
            <input
              type="range" min="0" max="50" value={debtChange}
              onChange={(e) => setDebtChange(Number(e.target.value))}
              className="w-full accent-primary cursor-pointer"
            />
          </div>

          <button
            onClick={runSimulation}
            disabled={loading || !selectedBorrowerId}
            className="w-full py-3 bg-primary text-primary-foreground font-semibold rounded-xl text-sm hover:bg-primary/90 transition-all flex items-center justify-center gap-2 disabled:opacity-50"
          >
            {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
            Run Scenario Simulation
          </button>
        </div>

        {/* Results Overview */}
        <div className="lg:col-span-2 space-y-6">

          {/* Calculation Status Badge */}
          {result && (
            <div className={`px-4 py-3 rounded-xl border text-xs font-semibold flex items-center gap-2 ${STATUS_COLORS[calcStatus]}`}>
              <Info className="w-4 h-4 shrink-0" />
              <span>Calculation Status: {STATUS_LABELS[calcStatus]}</span>
            </div>
          )}

          {/* Caveats Panel */}
          {result && result.caveats && result.caveats.length > 0 && (
            <div className="bg-amber-500/5 border border-amber-500/20 rounded-xl p-4 space-y-1.5">
              <p className="text-xs font-bold text-amber-400 flex items-center gap-1.5">
                <AlertTriangle className="w-3.5 h-3.5" /> Data Quality Notices
              </p>
              {result.caveats.map((c, i) => (
                <p key={i} className="text-xs text-amber-300/80 leading-relaxed pl-5">• {c}</p>
              ))}
            </div>
          )}

          {/* Top Result Banner */}
          {isInsufficient ? (
            <div className="p-6 rounded-2xl border bg-muted/20 border-border shadow-sm flex items-center gap-4">
              <AlertTriangle className="w-8 h-8 text-amber-400 shrink-0" />
              <div>
                <h3 className="font-extrabold text-lg text-foreground">Insufficient Data</h3>
                <p className="text-xs text-muted-foreground mt-1">
                  {result?.caveats?.[0] ?? "Upload and process financial documents to run stress scenarios."}
                </p>
              </div>
            </div>
          ) : (
            <div className={`p-6 rounded-2xl border ${
              result?.at_risk
                ? "bg-red-400/10 border-red-400/30 text-red-400"
                : "bg-emerald-400/10 border-emerald-400/30 text-emerald-400"
            } shadow-sm flex items-center justify-between`}>
              <div className="flex items-center gap-3">
                {result?.at_risk ? <AlertTriangle className="w-8 h-8" /> : <ShieldCheck className="w-8 h-8" />}
                <div>
                  <h3 className="font-extrabold text-lg">
                    {result?.at_risk ? "FACILITY AT RISK UNDER STRESS" : (result ? "FACILITY REMAINS RESILIENT" : "—")}
                  </h3>
                  <p className="text-xs opacity-90">
                    Projected covenant breaches: <strong>{result?.covenant_breaches_count ?? 0}</strong>
                  </p>
                </div>
              </div>
              <div className="text-right">
                <span className="text-xs uppercase font-semibold text-foreground">Stressed Default Prob</span>
                {/* RULE: null = Insufficient Data, not 0% */}
                <p className="text-3xl font-extrabold text-foreground">
                  {result?.projected_default_prob != null ? `${result.projected_default_prob}%` : "N/A"}
                </p>
              </div>
            </div>
          )}

          {/* Comparison Bar Chart */}
          <div className="bg-card border border-border p-6 rounded-2xl shadow-sm">
            <h4 className="font-bold text-sm mb-1 flex items-center gap-2">
              <BarChart2 className="w-4 h-4 text-primary" /> Baseline vs. Stressed Financial Ratios
            </h4>
            {(!result || isInsufficient) ? (
              <div className="h-64 flex items-center justify-center text-muted-foreground text-sm">
                Run a scenario to compare ratios.
              </div>
            ) : (
              <>
                <p className="text-xs text-muted-foreground mb-4">
                  N/A bars indicate the ratio could not be calculated for this scenario.
                </p>
                <div className="h-64 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={chartData}>
                      <XAxis dataKey="metric" stroke="#6b7280" fontSize={12} tickLine={false} />
                      <YAxis stroke="#6b7280" fontSize={12} tickLine={false} />
                      <Tooltip
                        contentStyle={{ backgroundColor: "#111827", borderColor: "#374151", borderRadius: "8px", color: "#fff" }}
                        formatter={(value) => {
                          if (value == null) return "N/A";
                          return `${Number(value).toFixed(2)}x`;
                        }}
                      />
                      <Legend />
                      <Bar dataKey="Baseline" fill="#3b82f6" radius={[4, 4, 0, 0]}>
                        {chartData.map((entry, index) => (
                          <Cell key={`baseline-${index}`} fill={entry.baselineAvailable ? "#3b82f6" : "#374151"} />
                        ))}
                      </Bar>
                      <Bar dataKey="Stressed" fill="#ef4444" radius={[4, 4, 0, 0]}>
                        {chartData.map((entry, index) => (
                          <Cell key={`stressed-${index}`} fill={entry.stressedAvailable ? "#ef4444" : "#374151"} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </>
            )}
          </div>

          {/* Ratio Summary Panel */}
          {result && !isInsufficient && (
            <div className="grid grid-cols-2 gap-4">
              {[
                { label: "Baseline Leverage", val: fmtRatio(result.details?.baseline?.leverage) },
                { label: "Stressed Leverage", val: fmtRatio(result.details?.stressed?.leverage) },
                { label: "Baseline Coverage", val: fmtRatio(result.details?.baseline?.coverage) },
                { label: "Stressed Coverage", val: fmtRatio(result.details?.stressed?.coverage) },
              ].map(({ label, val }) => (
                <div key={label} className="bg-card border border-border rounded-xl p-4">
                  <p className="text-xs text-muted-foreground font-semibold uppercase tracking-wider">{label}</p>
                  <p className={`text-2xl font-extrabold mt-1 ${val === "N/A" ? "text-muted-foreground" : "text-foreground"}`}>
                    {val}
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
