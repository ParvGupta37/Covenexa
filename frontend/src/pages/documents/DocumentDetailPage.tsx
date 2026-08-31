import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  ArrowLeft,
  FileText,
  Loader2,
  Cpu,
  Shield
} from "lucide-react";
import api from "@/lib/api";
import { StatusBadge } from "@/components/shared/StatusBadge";
import { EmptyState } from "@/components/shared/EmptyState";
import { ErrorState } from "@/components/shared/ErrorState";
import { formatCompactCurrency } from "@/utils/format";

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

export default function DocumentDetailPage() {
  const { agreementId } = useParams<{ agreementId: string }>();
  const navigate = useNavigate();

  const [doc, setDoc] = useState<DocumentStatus | null>(null);
  const [covenants, setCovenants] = useState<Covenant[]>([]);
  const [financials, setFinancials] = useState<FinancialMetric[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!agreementId) return;
    async function load() {
      try {
        const [docRes, covRes, finRes] = await Promise.all([
          api.get(`/api/v1/documents/${agreementId}`),
          api.get(`/api/v1/documents/${agreementId}/covenants`),
          api.get(`/api/v1/documents/${agreementId}/financials`),
        ]);
        setDoc(docRes.data);
        setCovenants(covRes.data || []);
        setFinancials(finRes.data || []);
      } catch (e: any) {
        setError(e.response?.data?.detail ?? "Failed to load document details.");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [agreementId]);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-[#6B7280]">
        <Loader2 className="w-8 h-8 animate-spin text-[#7C8DFB] mb-2" />
        <p className="text-xs font-semibold">Analyzing document contents...</p>
      </div>
    );
  }

  if (error || !doc) {
    return <ErrorState message={error || "Document not found."} onRetry={() => navigate("/app/uploads")} />;
  }

  const fileName = doc.file_path.split("/").pop() ?? doc.agreement_id;
  const latestFin = financials[0];

  return (
    <div className="space-y-8 pb-12">
      {/* Header */}
      <div>
        <button
          onClick={() => navigate("/app/uploads")}
          className="flex items-center gap-1 text-xs font-semibold text-[#6B7280] hover:text-[#111827] mb-3 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Documents</span>
        </button>

        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-2xl bg-[#E8ECFF] text-[#4F46E5] flex items-center justify-center shrink-0">
            <FileText className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-xl md:text-2xl font-bold text-[#111827] truncate">
              {fileName}
            </h1>
            <p className="text-xs font-medium text-[#6B7280] mt-0.5 capitalize">
              {doc.document_type.replace(/_/g, " ")} • Ingested {new Date(doc.upload_date).toLocaleDateString()}
            </p>
          </div>
        </div>
      </div>

      {/* Processing Pipeline Status */}
      <div className="bg-white rounded-2xl p-6 border border-[#EEF1F5] shadow-[0_4px_20px_rgba(17,24,39,0.04)] space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-bold text-[#111827] flex items-center gap-2">
            <Cpu className="w-4 h-4 text-[#7C8DFB]" />
            <span>Processing Pipeline Status</span>
          </h3>
          <StatusBadge status={doc.processing_status} />
        </div>
      </div>

      {/* Financial Metrics Highlights */}
      {latestFin && (
        <div className="space-y-4">
          <h3 className="text-sm font-bold text-[#111827]">
            Extracted Financial Highlights ({latestFin.reporting_period || "LTM"})
          </h3>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="bg-white p-4 rounded-2xl border border-[#EEF1F5]">
              <span className="text-xs font-semibold text-[#6B7280]">Revenue</span>
              <p className="text-xl font-bold text-[#111827] mt-1">
                {latestFin.revenue != null ? formatCompactCurrency(latestFin.revenue, latestFin.currency || "USD") : "N/A"}
              </p>
            </div>
            <div className="bg-white p-4 rounded-2xl border border-[#EEF1F5]">
              <span className="text-xs font-semibold text-[#6B7280]">EBITDA</span>
              <p className="text-xl font-bold text-[#111827] mt-1">
                {latestFin.ebitda != null ? formatCompactCurrency(latestFin.ebitda, latestFin.currency || "USD") : "N/A"}
              </p>
            </div>
            <div className="bg-white p-4 rounded-2xl border border-[#EEF1F5]">
              <span className="text-xs font-semibold text-[#6B7280]">Leverage Ratio</span>
              <p className="text-xl font-bold text-[#111827] mt-1">
                {latestFin.leverage_ratio != null ? `${latestFin.leverage_ratio.toFixed(2)}x` : "N/A"}
              </p>
            </div>
            <div className="bg-white p-4 rounded-2xl border border-[#EEF1F5]">
              <span className="text-xs font-semibold text-[#6B7280]">Interest Coverage</span>
              <p className="text-xl font-bold text-[#111827] mt-1">
                {latestFin.interest_coverage != null ? `${latestFin.interest_coverage.toFixed(2)}x` : "N/A"}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Extracted Covenants List */}
      <div className="space-y-4">
        <h3 className="text-sm font-bold text-[#111827]">
          Extracted Maintenance & Compliance Covenants ({covenants.length})
        </h3>
        {covenants.length === 0 ? (
          <EmptyState
            icon={Shield}
            title="No covenants extracted"
            description="No specific covenant terms identified in this document file."
          />
        ) : (
          <div className="space-y-3">
            {covenants.map((cov) => (
              <div key={cov.id} className="bg-white border border-[#EEF1F5] rounded-2xl p-5 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-sm text-[#111827]">{cov.name}</span>
                  <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-[#E8ECFF] text-[#4F46E5]">
                    {cov.covenant_type}
                  </span>
                </div>
                {cov.formula && (
                  <p className="text-xs text-[#6B7280] font-mono">Formula: {cov.formula}</p>
                )}
                {cov.threshold != null && (
                  <p className="text-xs text-[#111827]">Threshold Limit: {cov.threshold}x</p>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
