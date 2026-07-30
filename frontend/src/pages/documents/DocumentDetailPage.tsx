import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  ArrowLeft, FileText, Loader2, AlertCircle, CheckCircle2,
  Clock, Database, Cpu, ChevronDown, ChevronUp, TrendingUp,
  Shield, DollarSign, AlertTriangle, BookOpen, Hash,
} from "lucide-react";
import api from "@/lib/api";

// ── Types ───────────────────────────────────────────────────────────────────
interface DocumentStatus {
  agreement_id: string;
  loan_id: string;
  file_path: string;
  document_type: string;
  processing_status: string;
  processing_error?: string;
  processed_at?: string;
  page_count?: number;
  chunk_count?: number;
  upload_date: string;
}

interface Covenant {
  id: string;
  agreement_id: string;
  name: string;
  covenant_type: string;
  formula?: string;
  threshold?: number;
  threshold_direction?: string;
  frequency?: string;
  cure_period_days?: number;
  is_event_of_default: boolean;
  amendment_references?: string;
  raw_text?: string;
  extracted_at: string;
}

interface FinancialMetric {
  id: string;
  reporting_period?: string;
  revenue?: number;
  ebitda?: number;
  net_income?: number;
  total_debt?: number;
  cash?: number;
  interest_expense?: number;
  leverage_ratio?: number;
  interest_coverage?: number;
  currency: string;
  extracted_at: string;
}

// ── Helpers ────────────────────────────────────────────────────────────────
function fmt(val?: number, currency = "USD"): string {
  if (val == null) return "—";
  if (Math.abs(val) >= 1_000_000_000)
    return `${currency} ${(val / 1_000_000_000).toFixed(2)}B`;
  if (Math.abs(val) >= 1_000_000)
    return `${currency} ${(val / 1_000_000).toFixed(2)}M`;
  return `${currency} ${Number(val).toLocaleString()}`;
}

function fmtRatio(val?: number): string {
  if (val == null) return "—";
  return `${Number(val).toFixed(2)}x`;
}

const STATUS_STEPS = [
  { key: "pending",               label: "Queued" },
  { key: "parsing",               label: "OCR / Parse" },
  { key: "chunking",              label: "Chunking" },
  { key: "embedding",             label: "Embedding" },
  { key: "embedding_done",        label: "Indexed" },
  { key: "extracting",            label: "AI Extraction" },
  { key: "covenants_extracted",   label: "Covenants" },
  { key: "done",                  label: "Complete" },
];

function PipelineProgress({ status }: { status: string }) {
  const currentIdx = STATUS_STEPS.findIndex((s) => s.key === status);
  const isFailed = status === "failed";

  return (
    <div className="flex items-center gap-1 flex-wrap">
      {STATUS_STEPS.map((step, i) => {
        const done = !isFailed && i <= currentIdx;
        const active = !isFailed && i === currentIdx;
        return (
          <div key={step.key} className="flex items-center gap-1">
            <div className={`flex items-center gap-1 px-2 py-1 rounded text-xs font-medium border transition-all ${
              isFailed && i === 0
                ? "bg-destructive/10 border-destructive/30 text-destructive"
                : done
                  ? active
                    ? "bg-primary/20 border-primary text-primary animate-pulse"
                    : "bg-emerald-500/10 border-emerald-500/20 text-emerald-400"
                  : "bg-muted/40 border-border text-muted-foreground opacity-50"
            }`}>
              {active ? <Loader2 className="w-2.5 h-2.5 animate-spin" /> :
               done ? <CheckCircle2 className="w-2.5 h-2.5" /> :
               <Clock className="w-2.5 h-2.5" />}
              {step.label}
            </div>
            {i < STATUS_STEPS.length - 1 && (
              <div className={`w-3 h-px ${done && i < currentIdx ? "bg-emerald-500/40" : "bg-border"}`} />
            )}
          </div>
        );
      })}
      {isFailed && (
        <div className="flex items-center gap-1 px-2 py-1 rounded text-xs font-medium border bg-destructive/10 border-destructive/30 text-destructive">
          <AlertCircle className="w-2.5 h-2.5" /> Failed
        </div>
      )}
    </div>
  );
}

const COVENANT_TYPE_COLORS: Record<string, string> = {
  maintenance:  "text-blue-400 bg-blue-400/10 border-blue-400/20",
  incurrence:   "text-purple-400 bg-purple-400/10 border-purple-400/20",
  reporting:    "text-amber-400 bg-amber-400/10 border-amber-400/20",
  negative:     "text-rose-400 bg-rose-400/10 border-rose-400/20",
};

// ── Component ──────────────────────────────────────────────────────────────
export default function DocumentDetailPage() {
  const { agreementId } = useParams<{ agreementId: string }>();
  const navigate = useNavigate();

  const [doc, setDoc] = useState<DocumentStatus | null>(null);
  const [covenants, setCovenants] = useState<Covenant[]>([]);
  const [financials, setFinancials] = useState<FinancialMetric[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [expandedCovenant, setExpandedCovenant] = useState<string | null>(null);

  useEffect(() => {
    if (!agreementId) return;
    let active = true;

    async function load() {
      try {
        const [docRes, covRes, finRes] = await Promise.all([
          api.get(`/api/v1/documents/${agreementId}`),
          api.get(`/api/v1/documents/${agreementId}/covenants`),
          api.get(`/api/v1/documents/${agreementId}/financials`),
        ]);
        if (!active) return;
        setDoc(docRes.data);
        setCovenants(covRes.data);
        setFinancials(finRes.data);
      } catch (e: any) {
        if (active) setError(e.response?.data?.detail ?? "Failed to load document.");
      } finally {
        if (active) setLoading(false);
      }
    }
    load();

    // Re-poll if processing
    const interval = setInterval(async () => {
      if (!active || !doc) return;
      if (["done", "failed"].includes(doc.processing_status)) {
        clearInterval(interval);
        return;
      }
      try {
        const [docRes, covRes, finRes] = await Promise.all([
          api.get(`/api/v1/documents/${agreementId}`),
          api.get(`/api/v1/documents/${agreementId}/covenants`),
          api.get(`/api/v1/documents/${agreementId}/financials`),
        ]);
        if (!active) return;
        setDoc(docRes.data);
        setCovenants(covRes.data);
        setFinancials(finRes.data);
      } catch { /* silent */ }
    }, 6000);

    return () => { active = false; clearInterval(interval); };
  }, [agreementId]);

  // ── Loading ──
  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-64 gap-3 text-muted-foreground">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
        <p>Loading document analysis…</p>
      </div>
    );
  }

  if (error || !doc) {
    return (
      <div className="flex flex-col items-center justify-center h-64 gap-3">
        <AlertCircle className="w-8 h-8 text-destructive" />
        <p className="text-destructive font-medium">{error || "Document not found."}</p>
        <button onClick={() => navigate("/uploads")} className="text-primary text-sm underline">← Back to uploads</button>
      </div>
    );
  }

  const fileName = doc.file_path.split("/").pop() ?? doc.agreement_id;
  const latestFin = financials[0];

  return (
    <div className="space-y-8">

      {/* Header */}
      <div>
        <button
          onClick={() => navigate("/uploads")}
          className="flex items-center gap-1.5 text-muted-foreground hover:text-foreground text-sm mb-4 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" /> Back to Documents
        </button>
        <div className="flex items-start gap-4">
          <div className="p-3 bg-primary/10 rounded-xl border border-primary/20 text-primary">
            <FileText className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-2xl font-bold tracking-tight truncate">{fileName}</h1>
            <p className="text-muted-foreground text-sm mt-0.5 capitalize">
              {doc.document_type.replace(/_/g, " ")} · Uploaded {new Date(doc.upload_date).toLocaleDateString("en-US", { month: "long", day: "numeric", year: "numeric" })}
            </p>
          </div>
        </div>
      </div>

      {/* Pipeline Progress */}
      <div className="bg-card border border-border rounded-xl p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="font-semibold flex items-center gap-2">
            <Cpu className="w-4 h-4 text-primary" /> Processing Pipeline
          </h2>
          <div className="flex items-center gap-3 text-xs text-muted-foreground">
            {doc.page_count != null && <span className="flex items-center gap-1"><BookOpen className="w-3 h-3" />{doc.page_count} pages</span>}
            {doc.chunk_count != null && <span className="flex items-center gap-1"><Hash className="w-3 h-3" />{doc.chunk_count} chunks</span>}
          </div>
        </div>
        <PipelineProgress status={doc.processing_status} />
        {doc.processing_error && (
          <div className="p-3 bg-destructive/10 border border-destructive/20 text-destructive text-xs rounded-lg flex items-start gap-2">
            <AlertCircle className="w-3.5 h-3.5 shrink-0 mt-0.5" />
            <span>{doc.processing_error}</span>
          </div>
        )}
      </div>

      {/* Financial Metrics */}
      {latestFin ? (
        <div className="space-y-4">
          <h2 className="text-xl font-bold flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-primary" /> Financial Metrics
            {latestFin.reporting_period && (
              <span className="text-sm font-normal text-muted-foreground">— {latestFin.reporting_period}</span>
            )}
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { label: "Revenue",          value: fmt(Number(latestFin.revenue),          latestFin.currency), icon: DollarSign, color: "text-emerald-400" },
              { label: "EBITDA",           value: fmt(Number(latestFin.ebitda),           latestFin.currency), icon: TrendingUp, color: "text-blue-400" },
              { label: "Total Debt",       value: fmt(Number(latestFin.total_debt),       latestFin.currency), icon: Database,   color: "text-amber-400" },
              { label: "Cash",             value: fmt(Number(latestFin.cash),             latestFin.currency), icon: DollarSign, color: "text-teal-400" },
              { label: "Leverage Ratio",   value: fmtRatio(latestFin.leverage_ratio),                         icon: AlertTriangle, color: latestFin.leverage_ratio != null && latestFin.leverage_ratio > 4 ? "text-destructive" : "text-emerald-400" },
              { label: "Interest Coverage",value: fmtRatio(latestFin.interest_coverage),                      icon: Shield,    color: latestFin.interest_coverage != null && latestFin.interest_coverage < 2 ? "text-destructive" : "text-emerald-400" },
              { label: "Net Income",       value: fmt(Number(latestFin.net_income),       latestFin.currency), icon: TrendingUp, color: "text-violet-400" },
              { label: "Interest Expense", value: fmt(Number(latestFin.interest_expense), latestFin.currency), icon: Database,   color: "text-orange-400" },
            ].map(({ label, value, icon: Icon, color }) => (
              <div key={label} className="bg-card border border-border rounded-xl p-4 space-y-1">
                <div className={`w-8 h-8 rounded-lg flex items-center justify-center mb-2 ${color} bg-current/10`}>
                  <Icon className={`w-4 h-4 ${color}`} style={{ filter: "none" }} />
                </div>
                <p className="text-xs text-muted-foreground font-medium">{label}</p>
                <p className="text-lg font-bold">{value}</p>
              </div>
            ))}
          </div>
        </div>
      ) : doc.processing_status === "done" ? (
        <div className="bg-card border border-dashed border-border rounded-xl p-8 text-center text-muted-foreground">
          <TrendingUp className="w-8 h-8 mx-auto mb-2 opacity-30" />
          <p className="font-medium">No financial metrics extracted</p>
          <p className="text-sm">This may not be a financial statement, or the document had no identifiable figures.</p>
        </div>
      ) : null}

      {/* Covenants Table */}
      <div className="space-y-4">
        <h2 className="text-xl font-bold flex items-center gap-2">
          <Shield className="w-5 h-5 text-primary" /> Extracted Covenants
          <span className="text-sm font-normal text-muted-foreground">({covenants.length})</span>
        </h2>

        {covenants.length === 0 ? (
          <div className="bg-card border border-dashed border-border rounded-xl p-8 text-center text-muted-foreground">
            <Shield className="w-8 h-8 mx-auto mb-2 opacity-30" />
            <p className="font-medium">
              {["done", "covenants_extracted"].includes(doc.processing_status)
                ? "No covenants found in this document"
                : "Covenants will appear here once extraction is complete"}
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {covenants.map((cov) => {
              const isOpen = expandedCovenant === cov.id;
              return (
                <div key={cov.id} className="bg-card border border-border rounded-xl overflow-hidden transition-all hover:border-primary/20">
                  <button
                    className="w-full flex items-center gap-4 p-5 text-left"
                    onClick={() => setExpandedCovenant(isOpen ? null : cov.id)}
                  >
                    {/* Name & Type */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-3 flex-wrap">
                        <p className="font-semibold text-sm">{cov.name}</p>
                        <span className={`text-xs px-2 py-0.5 rounded-full border font-medium ${COVENANT_TYPE_COLORS[cov.covenant_type] ?? "text-muted-foreground bg-muted border-border"}`}>
                          {cov.covenant_type}
                        </span>
                        {cov.is_event_of_default && (
                          <span className="text-xs px-2 py-0.5 rounded-full border bg-destructive/10 border-destructive/20 text-destructive font-medium">
                            Event of Default
                          </span>
                        )}
                      </div>
                      {cov.formula && (
                        <p className="text-xs text-muted-foreground mt-1 truncate">{cov.formula}</p>
                      )}
                    </div>

                    {/* Threshold + Frequency */}
                    <div className="flex items-center gap-6 text-sm shrink-0">
                      {cov.threshold != null && (
                        <div className="text-right">
                          <p className="text-xs text-muted-foreground">Threshold</p>
                          <p className="font-bold">
                            {cov.threshold_direction === "max" ? "≤ " : cov.threshold_direction === "min" ? "≥ " : ""}
                            {cov.threshold}x
                          </p>
                        </div>
                      )}
                      {cov.frequency && (
                        <div className="text-right hidden md:block">
                          <p className="text-xs text-muted-foreground">Frequency</p>
                          <p className="font-medium capitalize">{cov.frequency.replace(/_/g, " ")}</p>
                        </div>
                      )}
                      {cov.cure_period_days != null && (
                        <div className="text-right hidden md:block">
                          <p className="text-xs text-muted-foreground">Cure Period</p>
                          <p className="font-medium">{cov.cure_period_days}d</p>
                        </div>
                      )}
                    </div>
                    {isOpen ? <ChevronUp className="w-4 h-4 text-muted-foreground shrink-0" /> : <ChevronDown className="w-4 h-4 text-muted-foreground shrink-0" />}
                  </button>

                  {/* Expanded detail */}
                  {isOpen && (
                    <div className="border-t border-border px-5 pb-5 pt-4 space-y-3 bg-muted/20">
                      {cov.raw_text && (
                        <div>
                          <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-1">Source Text</p>
                          <p className="text-xs text-muted-foreground leading-relaxed bg-background border border-border rounded-lg p-3 font-mono">
                            {cov.raw_text.slice(0, 600)}{cov.raw_text.length > 600 ? "…" : ""}
                          </p>
                        </div>
                      )}
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
                        {[
                          ["Covenant ID", cov.id.slice(0, 8) + "…"],
                          ["Extracted", new Date(cov.extracted_at).toLocaleDateString()],
                          ["Amendment Refs", cov.amendment_references ?? "None"],
                          ["Event of Default", cov.is_event_of_default ? "Yes" : "No"],
                        ].map(([k, v]) => (
                          <div key={k}>
                            <p className="text-muted-foreground">{k}</p>
                            <p className="font-medium text-foreground">{v}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
