import React, { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import {
  Upload,
  FileText,
  Globe,
  CheckCircle2,
  AlertCircle,
  Loader2,
  RefreshCw,
  ArrowRight,
  Plus,
  Building2,
} from "lucide-react";
import api from "@/lib/api";
import { useCompanyStore } from "@/store/company.store";
import { CreateFacilityModal } from "@/components/loans/CreateFacilityModal";
import { StatusBadge } from "@/components/shared/StatusBadge";


interface Loan {
  id: string;
  borrower_id: string;
  principal_amount: { amount: number; currency: string };
  interest_rate: number;
}

interface Agreement {
  agreement_id: string;
  loan_id: string;
  file_path: string;
  document_type: string;
  processing_status: string;
  processing_error?: string;
  upload_date: string;
}

export default function UploadsPage() {
  const navigate = useNavigate();
  const { selectedCompanyId, selectedCompany } = useCompanyStore();

  const [ingestMode, setIngestMode] = useState<"upload" | "sec">("upload");

  const [loans, setLoans] = useState<Loan[]>([]);
  const [selectedLoanId, setSelectedLoanId] = useState("");
  const [isCreateFacilityModalOpen, setIsCreateFacilityModalOpen] = useState(false);
  const fileType = "loan_agreement";

  const [file, setFile] = useState<File | null>(null);
  const [secUrl, setSecUrl] = useState("");

  const [loading, setLoading] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState("");
  const [uploadError, setUploadError] = useState("");

  const [agreements, setAgreements] = useState<Agreement[]>([]);
  const [docsLoading, setDocsLoading] = useState(false);

  const loadLoans = useCallback(async () => {
    if (!selectedCompanyId) {
      setLoans([]);
      setSelectedLoanId("");
      return;
    }
    try {
      const res = await api.get(`/api/v1/loans/?borrower_id=${selectedCompanyId}`);
      const companyLoans: Loan[] = res.data ?? [];

      if (companyLoans.length > 0) {
        setLoans(companyLoans);
        setSelectedLoanId((prev) => (companyLoans.some((l) => l.id === prev) ? prev : companyLoans[0].id));
      } else {
        setLoans([]);
        setSelectedLoanId("");
      }
    } catch (err) {
      console.error("Failed to load loans for company", err);
      setLoans([]);
      setSelectedLoanId("");
    }
  }, [selectedCompanyId]);

  useEffect(() => {
    loadLoans();
  }, [loadLoans]);

  const loadAgreements = useCallback(async () => {
    if (!selectedLoanId) {
      setAgreements([]);
      return;
    }
    setDocsLoading(true);
    try {
      const res = await api.get(`/api/v1/documents/loan/${selectedLoanId}`);
      setAgreements(res.data || []);
    } catch {
      setAgreements([]);
    } finally {
      setDocsLoading(false);
    }
  }, [selectedLoanId]);

  useEffect(() => {
    loadAgreements();
  }, [loadAgreements]);

  useEffect(() => {
    const inProgress = agreements.some(
      (a) => !["done", "failed"].includes(a.processing_status)
    );
    if (!inProgress) return;
    const timer = setInterval(loadAgreements, 3000);
    return () => clearInterval(timer);
  }, [agreements, loadAgreements]);

  const handleUploadSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setUploadSuccess("");
    setUploadError("");

    if (!selectedLoanId) {
      setUploadError("No loan facility selected. Create a loan facility before uploading and associating documents.");
      return;
    }

    const targetLoan = loans.find((l) => l.id === selectedLoanId && l.borrower_id === selectedCompanyId);
    if (!targetLoan) {
      setUploadError("Selected facility does not belong to the active target borrower.");
      return;
    }

    setLoading(true);

    try {
      if (ingestMode === "upload") {
        if (!file) {
          setUploadError("Please select a file.");
          setLoading(false);
          return;
        }
        const formData = new FormData();
        formData.append("loan_id", selectedLoanId);
        formData.append("file_type", fileType);
        formData.append("file", file);

        await api.post("/api/v1/uploads/", formData, {
          headers: { "Content-Type": "multipart/form-data" },
        });
        setUploadSuccess(`"${file.name}" uploaded successfully! Document pipeline triggered.`);
        setFile(null);
      } else {
        if (!secUrl.trim()) {
          setUploadError("Please enter a valid SEC EDGAR URL.");
          setLoading(false);
          return;
        }
        await api.post("/api/v1/uploads/sec-url", {
          loan_id: selectedLoanId,
          sec_url: secUrl,
          document_type: "sec_10k",
        });
        setUploadSuccess("SEC EDGAR filing submitted! Downloader and metric extractor triggered.");
        setSecUrl("");
      }
      setTimeout(loadAgreements, 1500);
    } catch (err: any) {
      setUploadError(err.response?.data?.detail ?? "Ingestion failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8 pb-12">
      {/* ── Page Header ─────────────────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold text-[#111827] tracking-tight">
            Document Ingestion & SEC EDGAR
          </h1>
          <p className="text-xs md:text-sm font-medium text-[#6B7280] mt-1">
            Ingest credit agreements, term sheets, or SEC filings directly for automated parsing.
          </p>
        </div>

        {selectedCompany && (
          <div className="flex items-center gap-2 bg-white border border-[#EEF1F5] px-3.5 py-2 rounded-xl text-xs font-semibold shadow-sm shrink-0">
            <Building2 className="w-4 h-4 text-[#7C8DFB]" />
            <span className="text-[#6B7280]">Target:</span>
            <span className="text-[#111827] font-bold">{selectedCompany.company_name}</span>
          </div>
        )}
      </div>



      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Form: File Ingestion (7 Cols) */}
        <div className="lg:col-span-7 bg-white rounded-2xl p-6 border border-[#EEF1F5] shadow-[0_4px_20px_rgba(17,24,39,0.04)] space-y-6">
          {/* Mode Toggle */}
          <div className="flex gap-2 p-1 bg-[#F8F9FC] border border-[#EEF1F5] rounded-xl">
            <button
              type="button"
              onClick={() => {
                setIngestMode("upload");
                setUploadSuccess("");
                setUploadError("");
              }}
              className={`flex-1 flex items-center justify-center gap-2 py-2 rounded-lg text-xs font-semibold transition-all ${
                ingestMode === "upload"
                  ? "bg-white text-[#111827] shadow-sm"
                  : "text-[#6B7280] hover:text-[#111827]"
              }`}
            >
              <Upload className="w-3.5 h-3.5 text-[#7C8DFB]" />
              <span>Upload Document</span>
            </button>

            <button
              type="button"
              onClick={() => {
                setIngestMode("sec");
                setUploadSuccess("");
                setUploadError("");
              }}
              className={`flex-1 flex items-center justify-center gap-2 py-2 rounded-lg text-xs font-semibold transition-all ${
                ingestMode === "sec"
                  ? "bg-white text-[#111827] shadow-sm"
                  : "text-[#6B7280] hover:text-[#111827]"
              }`}
            >
              <Globe className="w-3.5 h-3.5 text-[#7C8DFB]" />
              <span>SEC EDGAR URL</span>
            </button>
          </div>

          <form onSubmit={handleUploadSubmit} className="space-y-5">
            {/* Facility Selector */}
            <div className="space-y-2">
              <label className="text-xs font-bold text-[#111827]">
                Target Credit Facility *
              </label>

              {loans.length === 0 ? (
                <div className="p-5 border border-dashed border-[#E5E7EB] rounded-xl text-center space-y-2 bg-[#F8F9FC]">
                  <AlertCircle className="w-6 h-6 mx-auto text-[#F97316]" />
                  <p className="text-xs font-semibold text-[#111827]">
                    No loan facilities active for this borrower.
                  </p>
                  <button
                    type="button"
                    onClick={() => setIsCreateFacilityModalOpen(true)}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-[#7C8DFB] text-white text-xs font-semibold rounded-xl shadow-sm hover:bg-[#6366F1] transition-all"
                  >
                    <Plus className="w-3.5 h-3.5" />
                    <span>Create Facility</span>
                  </button>
                </div>
              ) : (
                <select
                  value={selectedLoanId}
                  onChange={(e) => setSelectedLoanId(e.target.value)}
                  className="w-full bg-[#F8F9FC] border border-[#EEF1F5] rounded-xl px-4 py-2.5 text-xs font-semibold text-[#111827] focus:outline-none focus:ring-2 focus:ring-[#7C8DFB]/50"
                >
                  {loans.map((l) => (
                    <option key={l.id} value={l.id}>
                      Facility #{l.id.slice(0, 8)} — {selectedCompany?.company_name || "Borrower"} ({l.principal_amount?.amount != null ? `$${Number(l.principal_amount.amount).toLocaleString()}` : "N/A"})
                    </option>
                  ))}
                </select>
              )}
            </div>

            {/* Mode 1: Local File Drag-and-Drop */}
            {ingestMode === "upload" && (
              <div className="space-y-2">
                <label className="text-xs font-bold text-[#111827]">
                  Select Agreement File (.PDF, .TXT, .DOCX) *
                </label>
                <div className="border-2 border-dashed border-[#EEF1F5] rounded-2xl p-8 text-center hover:border-[#7C8DFB] transition-all bg-[#F8F9FC]">
                  <FileText className="w-10 h-10 mx-auto text-[#7C8DFB] mb-2" />
                  <input
                    type="file"
                    accept=".pdf,.txt,.docx"
                    onChange={(e) => setFile(e.target.files?.[0] ?? null)}
                    className="hidden"
                    id="file-upload-input"
                  />
                  <label
                    htmlFor="file-upload-input"
                    className="cursor-pointer text-xs font-bold text-[#4F46E5] hover:underline"
                  >
                    Click to browse file
                  </label>
                  <p className="text-[11px] text-[#9CA3AF] mt-1">
                    Supports PDF, TXT, DOCX files up to 50MB
                  </p>
                  {file && (
                    <div className="mt-3 p-2.5 bg-white border border-[#EEF1F5] rounded-xl text-xs font-mono text-[#111827] inline-block">
                      Selected: {file.name} ({(file.size / 1024 / 1024).toFixed(2)} MB)
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Mode 2: SEC EDGAR Filing URL */}
            {ingestMode === "sec" && (
              <div className="space-y-2">
                <label className="text-xs font-bold text-[#111827]">
                  SEC EDGAR Direct Filing URL *
                </label>
                <input
                  type="url"
                  value={secUrl}
                  onChange={(e) => setSecUrl(e.target.value)}
                  placeholder="https://www.sec.gov/Archives/edgar/data/320193/000032019324000106/aapl-20240928.htm"
                  className="w-full bg-[#F8F9FC] border border-[#EEF1F5] rounded-xl px-4 py-2.5 text-xs font-medium text-[#111827] focus:outline-none focus:ring-2 focus:ring-[#7C8DFB]/50 placeholder:text-[#9CA3AF]"
                />
                <p className="text-[11px] text-[#6B7280]">
                  Enter direct filing URL from sec.gov. The downloader automatically parses covenants and financial statements.
                </p>
              </div>
            )}

            {/* Messages */}
            {uploadError && (
              <div className="p-3 bg-[#FEE2E2] text-[#EF4444] rounded-xl text-xs flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{uploadError}</span>
              </div>
            )}

            {uploadSuccess && (
              <div className="p-3 bg-[#D1FAE5] text-[#10B981] rounded-xl text-xs flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 shrink-0" />
                <span>{uploadSuccess}</span>
              </div>
            )}

            <button
              type="submit"
              disabled={loading || loans.length === 0}
              className="w-full py-3 bg-[#7C8DFB] hover:bg-[#6366F1] text-white font-semibold rounded-xl text-xs shadow-sm transition-all flex items-center justify-center gap-2 disabled:opacity-50"
            >
              {loading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Upload className="w-4 h-4" />
              )}
              <span>
                {ingestMode === "upload"
                  ? "Upload & Process Document"
                  : "Fetch & Extract SEC Filing"}
              </span>
            </button>
          </form>
        </div>

        {/* Right Panel: Facility Document History (5 Cols) */}
        <div className="lg:col-span-5 bg-white rounded-2xl p-6 border border-[#EEF1F5] shadow-[0_4px_20px_rgba(17,24,39,0.04)] flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4 pb-3 border-b border-[#EEF1F5]">
              <h3 className="text-sm font-bold text-[#111827]">
                Facility Document Pipeline
              </h3>
              <button
                onClick={loadAgreements}
                className="p-1 text-[#6B7280] hover:text-[#111827] rounded-lg transition-colors"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${docsLoading ? "animate-spin" : ""}`} />
              </button>
            </div>

            {agreements.length === 0 ? (
              <div className="text-center py-10 space-y-3">
                <FileText className="w-8 h-8 mx-auto text-[#9CA3AF] opacity-50" />
                <div>
                  <p className="text-xs font-bold text-[#111827]">No documents uploaded yet.</p>
                  <p className="text-xs text-[#6B7280] mt-1 leading-relaxed max-w-xs mx-auto">
                    Upload a credit agreement or SEC filing to begin document analysis. Extracted covenants and financial metrics will appear in risk monitoring.
                  </p>
                </div>
              </div>
            ) : (
              <div className="space-y-3 max-h-[420px] overflow-y-auto pr-1">
                {agreements.map((ag) => (
                  <div
                    key={ag.agreement_id}
                    onClick={() => navigate(`/app/documents/${ag.agreement_id}`)}
                    className="p-3.5 bg-[#F8F9FC] border border-[#EEF1F5] rounded-xl hover:border-[#7C8DFB] cursor-pointer transition-all space-y-2 group"
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-xs font-bold text-[#111827] group-hover:text-[#4F46E5] truncate max-w-[180px]">
                        {ag.file_path.split("/").pop() ?? ag.agreement_id.slice(0, 8)}
                      </span>
                      <StatusBadge status={ag.processing_status} />
                    </div>

                    <div className="flex items-center justify-between text-[11px] text-[#6B7280] pt-1">
                      <span>{new Date(ag.upload_date).toLocaleDateString()}</span>
                      <span className="font-semibold text-[#7C8DFB] flex items-center gap-1">
                        View Details <ArrowRight className="w-3 h-3" />
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      <CreateFacilityModal
        isOpen={isCreateFacilityModalOpen}
        onClose={() => setIsCreateFacilityModalOpen(false)}
        onSuccess={(newLoanId) => {
          loadLoans();
          setSelectedLoanId(newLoanId);
        }}
        defaultBorrowerId={selectedCompanyId}
      />
    </div>
  );
}
