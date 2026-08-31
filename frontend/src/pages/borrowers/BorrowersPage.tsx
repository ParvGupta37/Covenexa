import { useState, useEffect } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import {
  Users,
  Search,
  Plus,
  ChevronRight,
  FileText,
  BrainCircuit,
  X,
  Filter,
  Archive,
  RotateCcw,
  AlertCircle,
  Loader2,
  CheckCircle2,
} from "lucide-react";

import api from "@/lib/api";
import { Borrower } from "@/types";
import { useCompanyStore } from "@/store/company.store";
import { useAuthStore } from "@/store/auth.store";

import { BorrowerAvatar } from "@/components/shared/BorrowerAvatar";
import { RiskBadge } from "@/components/shared/RiskBadge";
import { StatusBadge } from "@/components/shared/StatusBadge";
import { EmptyState } from "@/components/shared/EmptyState";
import { ErrorState } from "@/components/shared/ErrorState";
import { CardSkeleton } from "@/components/shared/LoadingSkeleton";
import { formatCompactCurrency } from "@/utils/format";

interface BorrowerHealth {
  score: number | null;
  category: string;
  breakdown?: {
    financial_score: number | null;
    compliance_score: number | null;
    liquidity_score: number | null;
    leverage_score: number | null;
    trend_score: number | null;
  };
  history?: { score: number; calculated_at?: string; date_label?: string }[];
}

interface BorrowerDefault {
  default_probability: number | null;
  risk_category: string;
  risk_factors?: string[];
}

export default function BorrowersPage() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const { openRegisterModal, fetchCompanies } = useCompanyStore();
  const { user } = useAuthStore();

  const isAdmin = user?.role === "ADMIN";

  const [borrowers, setBorrowers] = useState<Borrower[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [successToast, setSuccessToast] = useState<string | null>(null);

  const [searchTerm, setSearchTerm] = useState("");
  const [filterRisk, setFilterRisk] = useState<string>("ALL");
  const [statusFilter, setStatusFilter] = useState<"ACTIVE" | "ARCHIVED" | "ALL">("ACTIVE");

  // Selected Borrower Detail Drawer State
  const [selectedBorrower, setSelectedBorrower] = useState<Borrower | null>(null);
  const [selectedHealth, setSelectedHealth] = useState<BorrowerHealth | null>(null);
  const [selectedDefault, setSelectedDefault] = useState<BorrowerDefault | null>(null);
  const [selectedFinancials, setSelectedFinancials] = useState<any | null>(null);
  const [selectedCovenants, setSelectedCovenants] = useState<any[]>([]);
  const [detailLoading, setDetailLoading] = useState(false);

  // Lifecycle Modals State
  const [borrowerToArchive, setBorrowerToArchive] = useState<Borrower | null>(null);
  const [archiveLoading, setArchiveLoading] = useState(false);
  const [archiveError, setArchiveError] = useState<string | null>(null);

  const [borrowerToRestore, setBorrowerToRestore] = useState<Borrower | null>(null);
  const [restoreLoading, setRestoreLoading] = useState(false);
  const [restoreError, setRestoreError] = useState<string | null>(null);

  const loadBorrowers = async (status: "ACTIVE" | "ARCHIVED" | "ALL" = statusFilter) => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.get(`/api/v1/borrowers/?status=${status}`);
      setBorrowers(res.data || []);

      // Check if URL search params specify a borrower
      const initialId = searchParams.get("selected");
      if (initialId && res.data) {
        const found = res.data.find((b: Borrower) => b.id === initialId);
        if (found) {
          openBorrowerDetail(found);
        }
      }
    } catch (err: any) {
      console.error("Failed to fetch borrowers:", err);
      setError("Failed to load portfolio borrowers.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadBorrowers(statusFilter);
  }, [statusFilter]);

  const openBorrowerDetail = async (borrower: Borrower) => {
    setSelectedBorrower(borrower);
    setDetailLoading(true);
    setSearchParams({ selected: borrower.id });

    try {
      const [healthRes, defaultRes, memoRes, covRes] = await Promise.all([
        api.get(`/api/v1/risk/health/${borrower.id}`).catch(() => ({ data: null })),
        api.get(`/api/v1/risk/default/${borrower.id}`).catch(() => ({ data: null })),
        api.get(`/api/v1/reports/credit-memo/${borrower.id}`).catch(() => ({ data: null })),
        api.get(`/api/v1/risk/covenants/${borrower.id}`).catch(() => ({ data: [] })),
      ]);

      setSelectedHealth(healthRes.data);
      setSelectedDefault(defaultRes.data);
      if (memoRes.data) {
        setSelectedFinancials(memoRes.data.financial_highlights || null);
      }
      setSelectedCovenants(covRes.data || []);
    } catch (err) {
      console.error("Error loading borrower details:", err);
    } finally {
      setDetailLoading(false);
    }
  };

  const closeDetail = () => {
    setSelectedBorrower(null);
    setSearchParams({});
  };

  const handleArchiveBorrower = async () => {
    if (!borrowerToArchive) return;
    setArchiveLoading(true);
    setArchiveError(null);

    try {
      await api.post(`/api/v1/borrowers/${borrowerToArchive.id}/archive`);

      // If the archived borrower was open in drawer, update or close it
      if (selectedBorrower?.id === borrowerToArchive.id) {
        setSelectedBorrower({ ...selectedBorrower, is_archived: true });
      }

      await loadBorrowers(statusFilter);
      await fetchCompanies();

      setSuccessToast(`Borrower "${borrowerToArchive.company_name}" archived successfully.`);
      setTimeout(() => setSuccessToast(null), 4000);
      setBorrowerToArchive(null);
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      setArchiveError(
        typeof detail === "string"
          ? detail
          : "Unable to archive borrower. Please try again."
      );
    } finally {
      setArchiveLoading(false);
    }
  };

  const handleRestoreBorrower = async () => {
    if (!borrowerToRestore) return;
    setRestoreLoading(true);
    setRestoreError(null);

    try {
      await api.post(`/api/v1/borrowers/${borrowerToRestore.id}/restore`);

      if (selectedBorrower?.id === borrowerToRestore.id) {
        setSelectedBorrower({ ...selectedBorrower, is_archived: false });
      }

      await loadBorrowers(statusFilter);
      await fetchCompanies();

      setSuccessToast(`Borrower "${borrowerToRestore.company_name}" restored to active portfolio.`);
      setTimeout(() => setSuccessToast(null), 4000);
      setBorrowerToRestore(null);
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      setRestoreError(
        typeof detail === "string"
          ? detail
          : "Unable to restore borrower. Please try again."
      );
    } finally {
      setRestoreLoading(false);
    }
  };

  // Filter logic
  const filteredBorrowers = borrowers.filter((b) => {
    const matchesSearch =
      b.company_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      b.sector.toLowerCase().includes(searchTerm.toLowerCase()) ||
      b.country.toLowerCase().includes(searchTerm.toLowerCase());

    if (filterRisk === "ALL") return matchesSearch;
    const level = b.risk_rating?.level?.toUpperCase() || "";
    if (filterRisk === "HIGH") return matchesSearch && (level === "HIGH" || level === "CRITICAL");
    if (filterRisk === "WATCH") return matchesSearch && (level === "MEDIUM" || level === "WATCH");
    if (filterRisk === "LOW") return matchesSearch && level === "LOW";
    return matchesSearch;
  });

  return (
    <div className="space-y-8 pb-12">
      {/* Success Toast */}
      {successToast && (
        <div className="fixed top-5 right-5 z-50 flex items-center gap-2 bg-emerald-600 text-white px-4 py-3 rounded-xl shadow-xl text-xs font-semibold animate-in fade-in slide-in-from-top-4">
          <CheckCircle2 className="w-4 h-4 shrink-0" />
          <span>{successToast}</span>
        </div>
      )}

      {/* ── Header Toolbar ────────────────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold text-[#111827] tracking-tight">
            Borrowers
          </h1>
          <p className="text-xs md:text-sm font-medium text-[#6B7280] mt-1">
            Monitor borrower health, risk ratings, and credit exposures across portfolio entities.
          </p>
        </div>

        <button
          onClick={openRegisterModal}
          className="flex items-center gap-2 px-4 py-2.5 bg-[#7C8DFB] hover:bg-[#6366F1] text-white font-semibold rounded-xl text-xs shadow-sm transition-all shrink-0"
        >
          <Plus className="w-4 h-4" />
          <span>Add Borrower</span>
        </button>
      </div>

      {/* ── Search & Filter Bar ───────────────────────────────────────── */}
      <div className="bg-white rounded-2xl p-4 border border-[#EEF1F5] shadow-[0_4px_20px_rgba(17,24,39,0.03)] flex flex-col md:flex-row items-center justify-between gap-4">
        {/* Search */}
        <div className="relative w-full md:w-80">
          <Search className="absolute left-3.5 top-2.5 w-4 h-4 text-[#9CA3AF]" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search borrower by name, sector, country..."
            className="w-full bg-[#F8F9FC] border border-[#EEF1F5] rounded-xl pl-10 pr-4 py-2 text-xs font-medium text-[#111827] focus:outline-none focus:ring-2 focus:ring-[#7C8DFB]/50 transition-all placeholder:text-[#9CA3AF]"
          />
        </div>

        {/* Lifecycle Status & Risk Filters */}
        <div className="flex items-center gap-4 w-full md:w-auto overflow-x-auto pb-1 md:pb-0">
          {/* Lifecycle Status Toggle */}
          <div className="inline-flex bg-[#F8F9FC] p-1 rounded-xl border border-[#EEF1F5] shrink-0">
            {(["ACTIVE", "ARCHIVED", "ALL"] as const).map((status) => (
              <button
                key={status}
                onClick={() => setStatusFilter(status)}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                  statusFilter === status
                    ? "bg-[#111827] text-white shadow-sm"
                    : "text-[#6B7280] hover:text-[#111827]"
                }`}
              >
                {status === "ACTIVE" ? "Active" : status === "ARCHIVED" ? "Archived" : "All"}
              </button>
            ))}
          </div>

          {/* Risk Filters */}
          <div className="flex items-center gap-2 shrink-0">
            <Filter className="w-3.5 h-3.5 text-[#9CA3AF] shrink-0" />
            {["ALL", "HIGH", "WATCH", "LOW"].map((cat) => (
              <button
                key={cat}
                onClick={() => setFilterRisk(cat)}
                className={`px-3 py-1.5 rounded-full text-xs font-semibold transition-all shrink-0 ${
                  filterRisk === cat
                    ? "bg-indigo-50 text-[#4F46E5] border border-indigo-200"
                    : "bg-[#F8F9FC] text-[#6B7280] hover:bg-[#E8ECFF] hover:text-[#111827]"
                }`}
              >
                {cat === "ALL" ? "All Risk" : cat === "HIGH" ? "High Risk" : cat === "WATCH" ? "Watchlist" : "Low Risk"}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* ── Borrowers Data Table ──────────────────────────────────────── */}
      {loading ? (
        <div className="bg-white rounded-2xl border border-[#EEF1F5] p-6 shadow-sm">
          <div className="space-y-4">
            <div className="h-6 bg-gray-200 rounded w-1/4 animate-pulse" />
            <div className="h-10 bg-gray-100 rounded w-full animate-pulse" />
            <div className="h-10 bg-gray-100 rounded w-full animate-pulse" />
            <div className="h-10 bg-gray-100 rounded w-full animate-pulse" />
          </div>
        </div>
      ) : error ? (
        <ErrorState message={error} onRetry={() => loadBorrowers(statusFilter)} />
      ) : filteredBorrowers.length === 0 ? (
        <EmptyState
          icon={Users}
          title={statusFilter === "ARCHIVED" ? "No Archived Borrowers" : "No Active Borrowers"}
          description={
            statusFilter === "ARCHIVED"
              ? "There are no archived borrowers in this portfolio."
              : "No active borrower profiles match your search criteria. Add a new borrower to begin monitoring."
          }
          actionText={statusFilter === "ACTIVE" ? "Add Borrower" : undefined}
          onAction={statusFilter === "ACTIVE" ? openRegisterModal : undefined}
        />
      ) : (
        <div className="bg-white rounded-2xl border border-[#EEF1F5] shadow-[0_4px_20px_rgba(17,24,39,0.03)] overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-[#F8F9FC] border-b border-[#EEF1F5] text-[11px] font-bold uppercase tracking-wider text-[#6B7280]">
                  <th className="py-3.5 px-6">Borrower</th>
                  <th className="py-3.5 px-4">Sector & Country</th>
                  <th className="py-3.5 px-4">Risk Rating</th>
                  <th className="py-3.5 px-4">Score Status</th>
                  <th className="py-3.5 px-6 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#EEF1F5] text-xs">
                {filteredBorrowers.map((b) => (
                  <tr
                    key={b.id}
                    onClick={() => openBorrowerDetail(b)}
                    className="hover:bg-[#F8F9FC] transition-colors cursor-pointer group"
                  >
                    <td className="py-4 px-6">
                      <div className="flex items-center gap-3">
                        <BorrowerAvatar name={b.company_name} size="md" />
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="font-bold text-[#111827] group-hover:text-[#4F46E5] transition-colors text-sm">
                              {b.company_name}
                            </span>
                            {b.is_archived && (
                              <span className="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase bg-slate-100 text-slate-600 border border-slate-200">
                                Archived
                              </span>
                            )}
                          </div>
                          <p className="text-[11px] text-[#9CA3AF] mt-0.5 font-mono">
                            ID: {b.id.slice(0, 8)}...
                          </p>
                        </div>
                      </div>
                    </td>

                    <td className="py-4 px-4 font-medium text-[#6B7280]">
                      <div>{b.sector}</div>
                      <div className="text-[11px] text-[#9CA3AF]">{b.country}</div>
                    </td>

                    <td className="py-4 px-4">
                      <RiskBadge category={b.risk_rating?.level || "WATCH"} />
                    </td>

                    <td className="py-4 px-4">
                      <div className="flex items-baseline gap-1">
                        <span className="text-base font-bold text-[#111827]">
                          {b.risk_rating?.score !== undefined ? b.risk_rating.score : "N/A"}
                        </span>
                        <span className="text-[10px] text-gray-400">/10</span>
                      </div>
                    </td>

                    <td className="py-4 px-6 text-right">
                      <div className="inline-flex items-center gap-2">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            openBorrowerDetail(b);
                          }}
                          className="inline-flex items-center gap-1 px-3 py-1.5 rounded-xl bg-[#F3F4FF] text-[#4F46E5] font-semibold hover:bg-[#E8ECFF] transition-colors text-xs"
                        >
                          <span>Inspect Profile</span>
                          <ChevronRight className="w-3.5 h-3.5" />
                        </button>

                        {isAdmin && !b.is_archived && (
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              setArchiveError(null);
                              setBorrowerToArchive(b);
                            }}
                            title="Archive Borrower"
                            className="p-1.5 rounded-xl text-gray-400 hover:text-amber-600 hover:bg-amber-50 transition-colors"
                          >
                            <Archive className="w-4 h-4" />
                          </button>
                        )}

                        {isAdmin && b.is_archived && (
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              setRestoreError(null);
                              setBorrowerToRestore(b);
                            }}
                            title="Restore Borrower"
                            className="p-1.5 rounded-xl text-gray-400 hover:text-emerald-600 hover:bg-emerald-50 transition-colors"
                          >
                            <RotateCcw className="w-4 h-4" />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ── BORROWER DETAIL PROFILE DRAWER / MODAL ─────────────────────── */}
      {selectedBorrower && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-sm z-50 flex justify-end transition-all">
          <div className="w-full max-w-3xl bg-[#F8F9FC] h-full overflow-y-auto p-6 md:p-8 shadow-2xl space-y-6 flex flex-col justify-between">
            <div>
              {/* Drawer Top Controls */}
              <div className="flex items-center justify-between border-b border-[#EEF1F5] pb-4 mb-6">
                <div className="flex items-center gap-3">
                  <BorrowerAvatar name={selectedBorrower.company_name} size="lg" />
                  <div>
                    <div className="flex items-center gap-2">
                      <h2 className="text-xl font-bold text-[#111827]">
                        {selectedBorrower.company_name}
                      </h2>
                      {selectedBorrower.is_archived && (
                        <span className="px-2.5 py-0.5 rounded-full text-xs font-bold uppercase bg-slate-200 text-slate-700">
                          Archived
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-[#6B7280]">
                      {selectedBorrower.sector} • {selectedBorrower.country}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  {isAdmin && !selectedBorrower.is_archived && (
                    <button
                      onClick={() => {
                        setArchiveError(null);
                        setBorrowerToArchive(selectedBorrower);
                      }}
                      className="p-2 rounded-xl text-gray-400 hover:text-amber-600 hover:bg-amber-50 transition-colors"
                      title="Archive Borrower"
                    >
                      <Archive className="w-4 h-4" />
                    </button>
                  )}

                  {isAdmin && selectedBorrower.is_archived && (
                    <button
                      onClick={() => {
                        setRestoreError(null);
                        setBorrowerToRestore(selectedBorrower);
                      }}
                      className="p-2 rounded-xl text-gray-400 hover:text-emerald-600 hover:bg-emerald-50 transition-colors"
                      title="Restore Borrower"
                    >
                      <RotateCcw className="w-4 h-4" />
                    </button>
                  )}

                  <button
                    onClick={closeDetail}
                    className="p-2 rounded-full hover:bg-gray-200 text-gray-500 transition-colors"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>
              </div>

              {/* Action Buttons Toolbar */}
              <div className="flex flex-wrap items-center gap-3 mb-6">
                <button
                  onClick={() => navigate(`/app/copilot?borrower_id=${selectedBorrower.id}`)}
                  className="flex items-center gap-2 px-4 py-2 bg-[#7C8DFB] text-white font-semibold rounded-xl text-xs hover:bg-[#6366F1] shadow-sm transition-all"
                >
                  <BrainCircuit className="w-4 h-4" />
                  <span>Ask Copilot</span>
                </button>

                <button
                  onClick={() => navigate(`/app/copilot?borrower_id=${selectedBorrower.id}&mode=memo`)}
                  className="flex items-center gap-2 px-4 py-2 bg-white border border-[#EEF1F5] text-[#111827] font-semibold rounded-xl text-xs hover:bg-gray-50 transition-all"
                >
                  <FileText className="w-4 h-4 text-[#7C8DFB]" />
                  <span>Generate Credit Memo</span>
                </button>

                <RiskBadge category={selectedBorrower.risk_rating?.level} />
              </div>

              {/* Detail Content Section */}
              {detailLoading ? (
                <div className="space-y-4">
                  <CardSkeleton />
                  <CardSkeleton />
                </div>
              ) : (
                <div className="space-y-6">
                  {/* KPI Row */}
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                    <div className="bg-white p-4 rounded-2xl border border-[#EEF1F5]">
                      <span className="text-xs font-semibold text-[#6B7280]">Health Score</span>
                      <p className="text-2xl font-bold text-[#111827] mt-1">
                        {selectedHealth?.score !== null && selectedHealth?.score !== undefined
                          ? selectedHealth.score.toFixed(1)
                          : "N/A"}
                      </p>
                      <span className="text-[10px] text-gray-400">Out of 100</span>
                    </div>

                    <div className="bg-white p-4 rounded-2xl border border-[#EEF1F5]">
                      <span className="text-xs font-semibold text-[#6B7280]">Default Prob.</span>
                      <p className="text-2xl font-bold text-[#EF4444] mt-1">
                        {selectedDefault?.default_probability !== null && selectedDefault?.default_probability !== undefined
                          ? `${selectedDefault.default_probability.toFixed(1)}%`
                          : "N/A"}
                      </p>
                      <span className="text-[10px] text-gray-400">Baseline calibrated</span>
                    </div>

                    <div className="bg-white p-4 rounded-2xl border border-[#EEF1F5]">
                      <span className="text-xs font-semibold text-[#6B7280]">Leverage Ratio</span>
                      <p className="text-2xl font-bold text-[#111827] mt-1">
                        {selectedFinancials?.leverage_ratio !== null && selectedFinancials?.leverage_ratio !== undefined
                          ? `${selectedFinancials.leverage_ratio.toFixed(2)}x`
                          : "N/A"}
                      </p>
                      <span className="text-[10px] text-gray-400">LTM Period</span>
                    </div>

                    <div className="bg-white p-4 rounded-2xl border border-[#EEF1F5]">
                      <span className="text-xs font-semibold text-[#6B7280]">Revenue</span>
                      <p className="text-2xl font-bold text-[#111827] mt-1">
                        {selectedFinancials?.revenue !== null && selectedFinancials?.revenue !== undefined
                          ? formatCompactCurrency(selectedFinancials.revenue, selectedFinancials.currency || "USD")
                          : "N/A"}
                      </p>
                      <span className="text-[10px] text-gray-400">Extracted metrics</span>
                    </div>
                  </div>

                  {/* Risk Factors Card */}
                  <div className="bg-white rounded-2xl p-5 border border-[#EEF1F5]">
                    <h4 className="text-xs font-bold uppercase tracking-wider text-[#6B7280] mb-3">
                      Risk Intelligence Drivers
                    </h4>
                    {selectedDefault?.risk_factors && selectedDefault.risk_factors.length > 0 ? (
                      <ul className="space-y-2">
                        {selectedDefault.risk_factors.map((rf, idx) => (
                          <li key={idx} className="flex items-start gap-2 text-xs text-[#111827]">
                            <span className="w-1.5 h-1.5 rounded-full bg-[#EF4444] mt-1.5 shrink-0" />
                            <span>{rf}</span>
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <p className="text-xs text-[#9CA3AF]">No specific risk drivers recorded.</p>
                    )}
                  </div>

                  {/* Covenants Summary Card */}
                  <div className="bg-white rounded-2xl p-5 border border-[#EEF1F5]">
                    <h4 className="text-xs font-bold uppercase tracking-wider text-[#6B7280] mb-3">
                      Covenant Monitoring Status
                    </h4>
                    {selectedCovenants.length > 0 ? (
                      <div className="space-y-3">
                        {selectedCovenants.map((cov: any) => (
                          <div key={cov.id} className="flex items-center justify-between p-3 rounded-xl bg-[#F8F9FC] text-xs">
                            <div>
                              <p className="font-bold text-[#111827]">{cov.covenant_name || "Maintenance Covenant"}</p>
                              <p className="text-[11px] text-[#6B7280] mt-0.5">
                                Current: {cov.current_value !== null ? `${cov.current_value}` : "N/A"} | Threshold: {cov.threshold_value}
                              </p>
                            </div>
                            <StatusBadge status={cov.status} />
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-xs text-[#9CA3AF]">No covenants active for this entity.</p>
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* Bottom Drawer Footer */}
            <div className="pt-4 border-t border-[#EEF1F5] flex justify-end">
              <button
                onClick={closeDetail}
                className="px-5 py-2.5 bg-[#111827] text-white font-semibold rounded-xl text-xs hover:bg-black transition-colors"
              >
                Done
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── ARCHIVE BORROWER CONFIRMATION MODAL ───────────────────────── */}
      {borrowerToArchive && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-in fade-in duration-150">
          <div className="bg-white border border-[#EEF1F5] w-full max-w-md rounded-2xl shadow-2xl p-6 space-y-5 animate-in zoom-in-95 duration-150">
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-amber-100 text-amber-700 flex items-center justify-center shrink-0">
                  <Archive className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-[#111827]">Archive borrower?</h3>
                  <p className="text-xs text-[#6B7280]">Historical data preservation</p>
                </div>
              </div>
              <button
                onClick={() => setBorrowerToArchive(null)}
                className="p-1 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="bg-amber-50/80 border border-amber-200/80 rounded-xl p-4 space-y-2 text-xs text-amber-900">
              <p className="font-semibold">
                You are archiving <strong className="text-amber-950 underline">{borrowerToArchive.company_name}</strong>.
              </p>
              <p className="text-amber-800">
                This will remove the borrower from your active portfolio while preserving its historical financial, risk, covenant, document, and audit data.
              </p>
            </div>

            {archiveError && (
              <div className="p-3 bg-red-50 border border-red-200 text-red-700 text-xs rounded-xl flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{archiveError}</span>
              </div>
            )}

            <div className="flex gap-3 pt-2">
              <button
                type="button"
                onClick={() => setBorrowerToArchive(null)}
                disabled={archiveLoading}
                className="flex-1 py-2.5 border border-[#EEF1F5] rounded-xl text-xs font-semibold text-[#6B7280] hover:bg-gray-50 transition-colors disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleArchiveBorrower}
                disabled={archiveLoading}
                className="flex-1 py-2.5 bg-amber-600 text-white text-xs font-semibold rounded-xl hover:bg-amber-700 transition-all flex items-center justify-center gap-2 disabled:opacity-50 shadow-sm"
              >
                {archiveLoading ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    <span>Archiving...</span>
                  </>
                ) : (
                  <>
                    <Archive className="w-3.5 h-3.5" />
                    <span>Archive Borrower</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── RESTORE BORROWER CONFIRMATION MODAL ───────────────────────── */}
      {borrowerToRestore && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-in fade-in duration-150">
          <div className="bg-white border border-[#EEF1F5] w-full max-w-md rounded-2xl shadow-2xl p-6 space-y-5 animate-in zoom-in-95 duration-150">
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-emerald-100 text-emerald-700 flex items-center justify-center shrink-0">
                  <RotateCcw className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-[#111827]">Restore borrower?</h3>
                  <p className="text-xs text-[#6B7280]">Return to active portfolio</p>
                </div>
              </div>
              <button
                onClick={() => setBorrowerToRestore(null)}
                className="p-1 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="bg-emerald-50/80 border border-emerald-200/80 rounded-xl p-4 space-y-2 text-xs text-emerald-900">
              <p className="font-semibold">
                You are restoring <strong className="text-emerald-950 underline">{borrowerToRestore.company_name}</strong>.
              </p>
              <p className="text-emerald-800">
                This will return the borrower to the active portfolio.
              </p>
            </div>

            {restoreError && (
              <div className="p-3 bg-red-50 border border-red-200 text-red-700 text-xs rounded-xl flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{restoreError}</span>
              </div>
            )}

            <div className="flex gap-3 pt-2">
              <button
                type="button"
                onClick={() => setBorrowerToRestore(null)}
                disabled={restoreLoading}
                className="flex-1 py-2.5 border border-[#EEF1F5] rounded-xl text-xs font-semibold text-[#6B7280] hover:bg-gray-50 transition-colors disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleRestoreBorrower}
                disabled={restoreLoading}
                className="flex-1 py-2.5 bg-emerald-600 text-white text-xs font-semibold rounded-xl hover:bg-emerald-700 transition-all flex items-center justify-center gap-2 disabled:opacity-50 shadow-sm"
              >
                {restoreLoading ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    <span>Restoring...</span>
                  </>
                ) : (
                  <>
                    <RotateCcw className="w-3.5 h-3.5" />
                    <span>Restore Borrower</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
