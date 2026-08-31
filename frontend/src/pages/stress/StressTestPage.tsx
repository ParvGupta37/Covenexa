import { useState, useEffect } from "react";
import { Sliders, Play, AlertTriangle, ShieldCheck, RefreshCw } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from "recharts";
import api from "@/lib/api";
import { useCompanyStore } from "@/store/company.store";
import { ImprovedEmptyState, InfoTooltip } from "@/components/shared/Explainer";

interface StressResult {
  projected_health_score: number | null;
  projected_default_prob: number | null;
  covenant_breaches_count: number;
  at_risk: boolean | null;
  calculation_status: "valid" | "partial_data" | "insufficient_data";
  caveats: string[];
  details: {
    baseline: {
      revenue?: number | null;
      debt?: number | null;
      leverage: number | null;
      coverage: number | null;
    };
    stressed: {
      revenue: number | null;
      ebitda: number | null;
      debt: number | null;
      interest?: number | null;
      leverage: number | null;
      coverage: number | null;
    };
    covenants_summary?: {
      total: number;
      breaches: number;
      unknown: number;
      compliant: number;
    };
  };
}

function formatFinancial(val: number | null | undefined, isCurrency = false): string {
  if (val === null || val === undefined) return "N/A";
  if (isCurrency) {
    if (Math.abs(val) >= 1_000_000_000) {
      return `$${(val / 1_000_000_000).toFixed(2)}B`;
    }
    if (Math.abs(val) >= 1_000_000) {
      return `$${(val / 1_000_000).toFixed(2)}M`;
    }
    return `$${val.toLocaleString()}`;
  }
  return val.toFixed(2);
}

// Labelled slider with context
function ScenarioSlider({
  label,
  tooltip,
  value,
  min,
  max,
  step,
  onChange,
  formatValue,
  valueColor,
}: {
  label: string;
  tooltip: string;
  value: number;
  min: number;
  max: number;
  step?: number;
  onChange: (v: number) => void;
  formatValue: (v: number) => string;
  valueColor: string;
}) {
  return (
    <div className="space-y-2">
      <div className="flex justify-between items-center text-xs font-semibold">
        <span className="flex items-center gap-0.5 text-[#6B7280]">
          {label}
          <InfoTooltip text={tooltip} />
        </span>
        <span style={{ color: valueColor }} className="font-bold">
          {formatValue(value)}
        </span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step || 1}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-full accent-[#7C8DFB] cursor-pointer"
      />
      <div className="flex justify-between text-[10px] text-[#9CA3AF]">
        <span>{formatValue(min)}</span>
        <span>Baseline: 0%</span>
        <span>{formatValue(max)}</span>
      </div>
    </div>
  );
}

// Baseline vs Stressed comparison row
function ComparisonRow({
  label,
  baseline,
  stressed,
  unit,
  tooltip,
  lowerIsBetter = false,
  isCurrency = false,
}: {
  label: string;
  baseline: number | null | undefined;
  stressed: number | null | undefined;
  unit?: string;
  tooltip: string;
  lowerIsBetter?: boolean;
  isCurrency?: boolean;
}) {
  const hasBoth = baseline != null && stressed != null;
  const change = hasBoth ? (stressed as number) - (baseline as number) : null;
  const isWorse = change !== null ? (lowerIsBetter ? change > 0 : change < 0) : false;

  return (
    <div className="flex items-center justify-between py-2.5 border-b border-[#EEF1F5] last:border-0">
      <span className="flex items-center gap-0.5 text-xs text-[#6B7280] font-medium">
        {label}
        <InfoTooltip text={tooltip} />
      </span>
      <div className="flex items-center gap-6 text-xs font-bold">
        <div className="text-right min-w-[70px]">
          <p className="text-[9px] text-[#9CA3AF] font-semibold uppercase tracking-wide">Baseline</p>
          <p className="text-[#111827]">
            {baseline != null ? `${formatFinancial(baseline, isCurrency)}${unit || ""}` : "N/A"}
          </p>
        </div>
        <div className="text-right min-w-[70px]">
          <p className="text-[9px] text-[#9CA3AF] font-semibold uppercase tracking-wide">Stressed</p>
          <p className={isWorse ? "text-[#EF4444]" : "text-[#10B981]"}>
            {stressed != null ? `${formatFinancial(stressed, isCurrency)}${unit || ""}` : "N/A"}
          </p>
        </div>
        <div className="text-right min-w-[70px]">
          <p className="text-[9px] text-[#9CA3AF] font-semibold uppercase tracking-wide">Δ Change</p>
          <p className={change != null ? (isWorse ? "text-[#EF4444]" : "text-[#10B981]") : "text-[#9CA3AF]"}>
            {change != null
              ? `${change > 0 ? "+" : ""}${formatFinancial(change, isCurrency)}${unit || ""}`
              : "N/A"}
          </p>
        </div>
      </div>
    </div>
  );
}

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

  const chartData = [
    {
      metric: "Leverage (×)",
      Baseline: result?.details?.baseline?.leverage ?? null,
      Stressed: result?.details?.stressed?.leverage ?? null,
    },
    {
      metric: "Coverage (×)",
      Baseline: result?.details?.baseline?.coverage ?? null,
      Stressed: result?.details?.stressed?.coverage ?? null,
    },
  ];

  const hasChartData = chartData.some((d) => d.Baseline !== null || d.Stressed !== null);

  return (
    <div className="space-y-8 pb-12">
      {/* Header */}
      <div>
        <h1 className="text-2xl md:text-3xl font-bold text-[#111827] tracking-tight">
          Stress Testing
        </h1>
        <p className="text-xs md:text-sm font-medium text-[#6B7280] mt-1">
          See how{" "}
          <strong className="text-[#111827]">
            {selectedCompany?.company_name || "the selected borrower"}
          </strong>{" "}
          could perform under adverse financial conditions.
        </p>
      </div>

      {!selectedBorrowerId ? (
        <ImprovedEmptyState
          icon={Sliders}
          title="No borrower selected"
          description="Select a borrower from the dropdown above to run a stress simulation and see scenario projections."
        />
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Sliders Panel (4 Cols) */}
          <div className="lg:col-span-4 bg-white rounded-2xl p-6 border border-[#EEF1F5] shadow-[0_4px_20px_rgba(17,24,39,0.04)] space-y-6">
            <div className="flex items-center gap-2 font-bold text-sm text-[#111827] pb-3 border-b border-[#EEF1F5]">
              <Sliders className="w-4 h-4 text-[#7C8DFB]" />
              <span>Scenario Controls</span>
            </div>

            <p className="text-[11px] text-[#6B7280] leading-relaxed -mt-2">
              Drag each slider to model an adverse scenario. Negative values mean contraction; positive means expansion.
            </p>

            <ScenarioSlider
              label="Revenue Change"
              tooltip="Simulates revenue growth or contraction. A -20% shock models a significant revenue decline, as might occur in an economic downturn."
              value={revenueChange}
              min={-50}
              max={20}
              onChange={setRevenueChange}
              formatValue={(v) => `${v}%`}
              valueColor={revenueChange < 0 ? "#EF4444" : "#10B981"}
            />

            <ScenarioSlider
              label="EBITDA Change"
              tooltip="EBITDA (Earnings Before Interest, Tax, Depreciation & Amortisation) measures operating profitability. A negative shock models rising costs or margin compression."
              value={ebitdaChange}
              min={-50}
              max={20}
              onChange={setEbitdaChange}
              formatValue={(v) => `${v}%`}
              valueColor={ebitdaChange < 0 ? "#EF4444" : "#10B981"}
            />

            <ScenarioSlider
              label="Interest Rate Shock"
              tooltip="Models a central bank rate increase, raising the borrower's interest expense. Measured in basis points (100 bps = 1%). A +200 bps shock is a significant rate hike scenario."
              value={rateChangeBps}
              min={0}
              max={600}
              step={50}
              onChange={setRateChangeBps}
              formatValue={(v) => `+${v} bps`}
              valueColor="#F97316"
            />

            <ScenarioSlider
              label="Additional Debt Load"
              tooltip="Models the borrower taking on additional debt. This increases leverage ratios and reduces headroom to covenant thresholds."
              value={debtChange}
              min={0}
              max={50}
              onChange={setDebtChange}
              formatValue={(v) => `+${v}%`}
              valueColor="#4F46E5"
            />

            <button
              onClick={runSimulation}
              disabled={loading || !selectedBorrowerId}
              className="w-full py-3 bg-[#7C8DFB] hover:bg-[#6366F1] text-white font-semibold rounded-xl text-xs shadow-sm transition-all flex items-center justify-center gap-2 disabled:opacity-50"
            >
              {loading ? (
                <RefreshCw className="w-4 h-4 animate-spin" />
              ) : (
                <Play className="w-4 h-4" />
              )}
              <span>Run Simulation</span>
            </button>
          </div>

          {/* Results (8 Cols) */}
          <div className="lg:col-span-8 space-y-6">
            {/* Result Banner */}
            {result ? (
              <>
                {result.at_risk === true ? (
                  <div className="p-6 rounded-2xl border shadow-sm flex items-center justify-between bg-[#FEE2E2]/40 border-[#FCA5A5] text-[#EF4444]">
                    <div className="flex items-center gap-3">
                      <AlertTriangle className="w-8 h-8 shrink-0 text-[#EF4444]" />
                      <div>
                        <h3 className="font-bold text-lg text-[#111827]">
                          Facility At Risk Under This Scenario
                        </h3>
                        <p className="text-xs text-[#6B7280] mt-0.5">
                          {result.covenant_breaches_count} projected covenant breach
                          {result.covenant_breaches_count !== 1 ? "es" : ""} under this scenario.
                        </p>
                      </div>
                    </div>

                    <div className="text-right shrink-0">
                      <span className="text-[10px] font-bold uppercase tracking-wider text-[#6B7280]">
                        Stressed Default Prob
                      </span>
                      <p className="text-3xl font-bold text-[#111827]">
                        {result.projected_default_prob != null
                          ? `${result.projected_default_prob.toFixed(1)}%`
                          : "N/A"}
                      </p>
                    </div>
                  </div>
                ) : result.at_risk === false ? (
                  <div className="p-6 rounded-2xl border shadow-sm flex items-center justify-between bg-[#D1FAE5]/40 border-[#6EE7B7] text-[#10B981]">
                    <div className="flex items-center gap-3">
                      <ShieldCheck className="w-8 h-8 shrink-0 text-[#10B981]" />
                      <div>
                        <h3 className="font-bold text-lg text-[#111827]">
                          Facility Remains Resilient
                        </h3>
                        <p className="text-xs text-[#6B7280] mt-0.5">
                          All monitored covenants evaluated and projected compliant under this scenario.
                        </p>
                      </div>
                    </div>

                    <div className="text-right shrink-0">
                      <span className="text-[10px] font-bold uppercase tracking-wider text-[#6B7280]">
                        Stressed Default Prob
                      </span>
                      <p className="text-3xl font-bold text-[#111827]">
                        {result.projected_default_prob != null
                          ? `${result.projected_default_prob.toFixed(1)}%`
                          : "N/A"}
                      </p>
                    </div>
                  </div>
                ) : (
                  <div className="p-6 rounded-2xl border shadow-sm flex items-center justify-between bg-[#FEF3C7]/40 border-[#FCD34D] text-[#D97706]">
                    <div className="flex items-center gap-3">
                      <AlertTriangle className="w-8 h-8 shrink-0 text-[#D97706]" />
                      <div>
                        <h3 className="font-bold text-lg text-[#111827]">
                          Unable to Determine Covenant Impact
                        </h3>
                        <p className="text-xs text-[#6B7280] mt-0.5">
                          Required financial ratios (EBITDA / coverage) are unavailable to evaluate covenant thresholds.
                        </p>
                      </div>
                    </div>

                    <div className="text-right shrink-0">
                      <span className="text-[10px] font-bold uppercase tracking-wider text-[#6B7280]">
                        Stressed Default Prob
                      </span>
                      <p className="text-3xl font-bold text-[#111827]">
                        {result.projected_default_prob != null
                          ? `${result.projected_default_prob.toFixed(1)}%`
                          : "N/A"}
                      </p>
                    </div>
                  </div>
                )}

                {/* Baseline vs Stressed Comparison */}
                <div className="bg-white rounded-2xl p-6 border border-[#EEF1F5] shadow-[0_4px_20px_rgba(17,24,39,0.04)]">
                  <h3 className="text-sm font-bold text-[#111827] mb-1">
                    Baseline vs. Stressed — Financial Position & Ratios
                  </h3>
                  <p className="text-xs text-[#6B7280] mb-5">
                    How key metrics and debt burden shift under the simulated scenario.
                  </p>

                  <ComparisonRow
                    label="Revenue (Total Net Sales)"
                    baseline={result.details?.baseline?.revenue}
                    stressed={result.details?.stressed?.revenue}
                    tooltip="Top-line operational revenue under the simulated contraction or expansion."
                    lowerIsBetter={false}
                    isCurrency={true}
                  />

                  <ComparisonRow
                    label="Total Debt Burden"
                    baseline={result.details?.baseline?.debt}
                    stressed={result.details?.stressed?.debt}
                    tooltip="Total debt outstanding including additional simulated debt load."
                    lowerIsBetter={true}
                    isCurrency={true}
                  />

                  <ComparisonRow
                    label="Leverage Ratio (Total Debt / EBITDA)"
                    baseline={result.details?.baseline?.leverage ?? null}
                    stressed={result.details?.stressed?.leverage ?? null}
                    unit="×"
                    tooltip="Measures total debt relative to earnings. Higher leverage = greater financial risk. Most covenants cap leverage at 3–5×."
                    lowerIsBetter={true}
                  />

                  <ComparisonRow
                    label="Interest Coverage (EBITDA / Interest)"
                    baseline={result.details?.baseline?.coverage ?? null}
                    stressed={result.details?.stressed?.coverage ?? null}
                    unit="×"
                    tooltip="Measures ability to service debt with operating earnings. Below 1.5× is typically distressed. Many covenants require a minimum of 2–3×."
                    lowerIsBetter={false}
                  />
                </div>

                {/* Chart */}
                <div className="bg-white rounded-2xl p-6 border border-[#EEF1F5] shadow-[0_4px_20px_rgba(17,24,39,0.04)]">
                  <h3 className="text-sm font-bold text-[#111827] mb-4">
                    Ratio Comparison Chart
                  </h3>
                  {hasChartData ? (
                    <div className="h-52 w-full">
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={chartData}>
                          <XAxis dataKey="metric" axisLine={false} tickLine={false} tick={{ fontSize: 11, fill: "#9CA3AF" }} />
                          <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 11, fill: "#9CA3AF" }} />
                          <Tooltip contentStyle={{ backgroundColor: "#111827", borderRadius: "8px", border: "none", color: "#FFF", fontSize: "12px" }} />
                          <Legend />
                          <Bar dataKey="Baseline" fill="#7C8DFB" radius={[6, 6, 0, 0]} />
                          <Bar dataKey="Stressed" fill="#EF4444" radius={[6, 6, 0, 0]} />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  ) : (
                    <div className="py-6 flex flex-col items-center justify-center text-center bg-[#F8F9FC] rounded-xl border border-dashed border-[#EEF1F5]">
                      <Sliders className="w-6 h-6 text-[#9CA3AF] mb-2" />
                      <p className="text-xs font-semibold text-[#6B7280]">Ratios Unavailable for Charting</p>
                      <p className="text-[11px] text-[#9CA3AF] max-w-sm mt-1">
                        Leverage and Interest Coverage cannot be projected because baseline EBITDA is unavailable for this borrower.
                      </p>
                    </div>
                  )}
                </div>

                {/* Caveats */}
                {result.caveats && result.caveats.length > 0 && (
                  <div className="p-4 bg-[#F8F9FC] border border-[#EEF1F5] rounded-2xl space-y-1.5">
                    <p className="text-[11px] font-bold text-[#6B7280] uppercase tracking-wide">
                      Data Caveats & Methodology Notes
                    </p>
                    {result.caveats.map((c, i) => (
                      <p key={i} className="text-[11px] text-[#9CA3AF] leading-relaxed flex items-start gap-1.5">
                        <span className="mt-0.5 shrink-0 text-[#D97706]">⚠</span>
                        {c}
                      </p>
                    ))}
                  </div>
                )}
              </>
            ) : (
              <ImprovedEmptyState
                icon={Sliders}
                title="No scenario run yet"
                description="Adjust scenario controls and click Run Simulation to evaluate how the borrower's financial position could change under stress."
                actionLabel="Run Simulation"
                onAction={runSimulation}
              />
            )}
          </div>
        </div>
      )}
    </div>
  );
}
