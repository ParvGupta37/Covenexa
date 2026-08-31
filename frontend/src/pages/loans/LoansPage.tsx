import { useState, useEffect } from "react";
import {
  Coins,
  Plus,
  Building2,
  Search,
  CheckCircle2,
  Archive,
  RotateCcw,
  AlertCircle,
  Loader2,
  X,
} from "lucide-react";
import api from "@/lib/api";
import { Loan } from "@/types";
import { useCompanyStore } from "@/store/company.store";
import { useAuthStore } from "@/store/auth.store";
import { CreateFacilityModal } from "@/components/loans/CreateFacilityModal";

import { KpiCard } from "@/components/shared/KpiCard";
import { StatusBadge } from "@/components/shared/StatusBadge";
import { EmptyState } from "@/components/shared/EmptyState";
import { ErrorState } from "@/components/shared/ErrorState";
import { formatCurrency, formatCompactCurrency } from "@/utils/format";

export default function LoansPage() {
  const { companies, selectedCompanyId, selectedCompany, fetchCompanies } =
    useCompanyStore();
  const { user } = useAuthStore();

  const isAdmin = user?.role === "ADMIN";

  const [loans, setLoans] = useState<Loan[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [successToast, setSuccessToast] = useState<string | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState<"ACTIVE" | "ARCHIVED" | "ALL">("ACTIVE");

  // Lifecycle Modals State
  const [loanToArchive, setLoanToArchive] = useState<Loan | null>(null);
  const [archiveLoading, setArchiveLoading] = useState(false);
  const [archiveError, setArchiveError] = useState<string | null>(null);

  const [loanToRestore, setLoanToRestore] = useState<Loan | null>(null);
  const [restoreLoading, setRestoreLoading] = useState(false);
  const [restoreError, setRestoreError] = useState<string | null>(null);

  useEffect(() => {
    fetchCompanies();
  }, [fetchCompanies]);

  async function loadLoans(status: "ACTIVE" | "ARCHIVED" | "ALL" = statusFilter) {
    setLoading(true);
    setError(null);
    try {
      const url = selectedCompanyId
        ? `/api/v1/loans/?borrower_id=${selectedCompanyId}&status=${status}`
        : `/api/v1/loans/?status=${status}`;
      const res = await api.get(url);
      setLoans(res.data || []);
    } catch (err: any) {
      console.error("Failed to load loans", err);
      setError("Failed to load credit facilities.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadLoans(statusFilter);
  }, [selectedCompanyId, statusFilter]);

  const handleArchiveLoan = async () => {
    if (!loanToArchive) return;
    setArchiveLoading(true);
    setArchiveError(null);

    try {
      await api.post(`/api/v1/loans/${loanToArchive.id}/archive`);
      await loadLoans(statusFilter);

      setSuccessToast(`Credit facility #${loanToArchive.id.slice(0, 8)} archived successfully.`);
      setTimeout(() => setSuccessToast(null), 4000);
      setLoanToArchive(null);
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      setArchiveError(
        typeof detail === "string"
          ? detail
          : "Unable to archive credit facility. Please try again."
      );
    } finally {
      setArchiveLoading(false);
    }
  };

  const handleRestoreLoan = async () => {
    if (!loanToRestore) return;
    setRestoreLoading(true);
    setRestoreError(null);

    try {
      await api.post(`/api/v1/loans/${loanToRestore.id}/restore`);
      await loadLoans(statusFilter);

      setSuccessToast(`Credit facility #${loanToRestore.id.slice(0, 8)} restored to active portfolio.`);
      setTimeout(() => setSuccessToast(null), 4000);
      setLoanToRestore(null);
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      setRestoreError(
        typeof detail === "string"
          ? detail
          : "Unable to restore credit facility. Please try again."
      );
    } finally {
      setRestoreLoading(false);
    }
  };

  // Compute facility metrics (active only)
  const activeLoans = loans.filter((l) => !l.is_archived);
  const totalFacilities = activeLoans.length;

  const currencyTotals = activeLoans.reduce<Record<string, number>>((acc, l) => {
    const amt = l.principal_amount?.amount ? Number(l.principal_amount.amount) : 0;
    const cur = (l.principal_amount?.currency || "USD").toUpperCase();
    acc[cur] = (acc[cur] || 0) + amt;
    return acc;
  }, {});
  const distinctCurrencies = Object.keys(currencyTotals);
  const primaryCurrency = distinctCurrencies[0] || "USD";

  const formattedTotalExposure =
    activeLoans.length === 0
      ? "N/A"
      : distinctCurrencies.length === 1
      ? formatCompactCurrency(currencyTotals[primaryCurrency], primaryCurrency)
      : distinctCurrencies
          .map((c) => formatCompactCurrency(currencyTotals[c], c))
          .join(" + ");

  const activeLoansCount = activeLoans.filter((l) => l.status === "ACTIVE").length;

  const filteredLoans = loans.filter((l) => {
    const borrowerName =
      companies.find((c) => c.id === l.borrower_id)?.company_name || "";
    return (
      l.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      borrowerName.toLowerCase().includes(searchTerm.toLowerCase())
    );
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

      {/* ── Page Header ─────────────────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold text-[#111827] tracking-tight">
            Loans & Credit Facilities
          </h1>
          <p className="text-xs md:text-sm font-medium text-[#6B7280] mt-1">
            Monitor credit facilities, interest rates, and compliance parameters across{" "}
            <strong className="text-[#111827]">
              {selectedCompany?.company_name || "all portfolio entities"}
            </strong>.
          </p>
        </div>

        <button
          onClick={() => setIsModalOpen(true)}
          className="flex items-center gap-2 px-4 py-2.5 bg-[#7C8DFB] hover:bg-[#6366F1] text-white font-semibold rounded-xl text-xs shadow-sm transition-all shrink-0"
        >
          <Plus className="w-4 h-4" />
          <span>Create Facility</span>
        </button>
      </div>

      {/* ── KPI Summary Cards ────────────────────────────────────────── */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-5">
        <KpiCard
          title="Active Facilities"
          value={totalFacilities}
          badgeText="Active Portfolio"
          badgeType="success"
          icon={Coins}
          iconBgColor="#E8ECFF"
          iconColor="#4F46E5"
        />

        <KpiCard
          title="Total Active Exposure"
          value={formattedTotalExposure}
          trendText="Principal committed"
          trendUp={false}
          icon={Building2}
          iconBgColor="#D1FAE5"
          iconColor="#10B981"
        />

        <KpiCard
          title="Performing Facilities"
          value={activeLoansCount}
          badgeText="Compliant"
          badgeType="success"
          icon={CheckCircle2}
          iconBgColor="#FEF3C7"
          iconColor="#D97706"
        />
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
            placeholder="Search facility ID or borrower name..."
            className="w-full bg-[#F8F9FC] border border-[#EEF1F5] rounded-xl pl-10 pr-4 py-2 text-xs font-medium text-[#111827] focus:outline-none focus:ring-2 focus:ring-[#7C8DFB]/50 transition-all placeholder:text-[#9CA3AF]"
          />
        </div>

        {/* Status Toggle */}
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
      </div>

      {/* ── Loans Data Table ─────────────────────────────────────────── */}
      {loading ? (
        <div className="bg-white rounded-2xl border border-[#EEF1F5] p-6 shadow-sm">
          <div className="space-y-3">
            <div className="h-6 bg-gray-200 rounded w-1/4 animate-pulse" />
            <div className="h-10 bg-gray-100 rounded w-full animate-pulse" />
            <div className="h-10 bg-gray-100 rounded w-full animate-pulse" />
          </div>
        </div>
      ) : error ? (
        <ErrorState message={error} onRetry={() => loadLoans(statusFilter)} />
      ) : filteredLoans.length === 0 ? (
        <EmptyState
          icon={Coins}
          title={statusFilter === "ARCHIVED" ? "No Archived Facilities" : "No Active Credit Facilities"}
          description={
            statusFilter === "ARCHIVED"
              ? "There are no archived credit facilities in this portfolio."
              : "No credit facilities found for this selection. Create a new facility to track agreement terms."
          }
          actionText={statusFilter === "ACTIVE" ? "Create Facility" : undefined}
          onAction={statusFilter === "ACTIVE" ? () => setIsModalOpen(true) : undefined}
        />
      ) : (
        <div className="bg-white rounded-2xl border border-[#EEF1F5] shadow-[0_4px_20px_rgba(17,24,39,0.03)] overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-[#F8F9FC] border-b border-[#EEF1F5] text-[11px] font-bold uppercase tracking-wider text-[#6B7280]">
                  <th className="py-3.5 px-6">Facility ID</th>
                  <th className="py-3.5 px-4">Borrower Entity</th>
                  <th className="py-3.5 px-4">Principal Amount</th>
                  <th className="py-3.5 px-4">Interest Rate</th>
                  <th className="py-3.5 px-4">Maturity Date</th>
                  <th className="py-3.5 px-4">Status</th>
                  <th className="py-3.5 px-6 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#EEF1F5] text-xs">
                {filteredLoans.map((l) => {
                  const borrowerName =
                    companies.find((c) => c.id === l.borrower_id)
                      ?.company_name || "Borrower Entity";

                  return (
                    <tr
                      key={l.id}
                      className="hover:bg-[#F8F9FC] transition-colors"
                    >
                      <td className="py-4 px-6 font-mono font-bold text-[#111827]">
                        <div className="flex items-center gap-2">
                          <span>#{l.id.slice(0, 8)}</span>
                          {l.is_archived && (
                            <span className="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase bg-slate-100 text-slate-600 border border-slate-200">
                              Archived
                            </span>
                          )}
                        </div>
                      </td>

                      <td className="py-4 px-4 font-semibold text-[#111827]">
                        {borrowerName}
                      </td>

                      <td className="py-4 px-4 font-bold text-[#111827]">
                        {formatCurrency(l.principal_amount?.amount, l.principal_amount?.currency)}
                      </td>

                      <td className="py-4 px-4 font-medium text-[#6B7280]">
                        {(l.interest_rate * 100).toFixed(2)}%
                      </td>

                      <td className="py-4 px-4 font-medium text-[#6B7280]">
                        {l.maturity_date || "N/A"}
                      </td>

                      <td className="py-4 px-4">
                        <StatusBadge status={l.is_archived ? "CLOSED" : l.status} />
                      </td>

                      <td className="py-4 px-6 text-right">
                        <div className="inline-flex items-center gap-2 justify-end">
                          {l.agreement_id ? (
                            <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-[#4F46E5] bg-[#E8ECFF] px-2.5 py-1 rounded-full">
                              Document Linked
                            </span>
                          ) : (
                            <span className="text-[11px] text-[#9CA3AF]">
                              Pending Ingestion
                            </span>
                          )}

                          {isAdmin && !l.is_archived && (
                            <button
                              onClick={() => {
                                setArchiveError(null);
                                setLoanToArchive(l);
                              }}
                              title="Archive Facility"
                              className="p-1.5 rounded-xl text-gray-400 hover:text-amber-600 hover:bg-amber-50 transition-colors ml-1"
                            >
                              <Archive className="w-4 h-4" />
                            </button>
                          )}

                          {isAdmin && l.is_archived && (
                            <button
                              onClick={() => {
                                setRestoreError(null);
                                setLoanToRestore(l);
                              }}
                              title="Restore Facility"
                              className="p-1.5 rounded-xl text-gray-400 hover:text-emerald-600 hover:bg-emerald-50 transition-colors ml-1"
                            >
                              <RotateCcw className="w-4 h-4" />
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <CreateFacilityModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSuccess={() => loadLoans(statusFilter)}
      />

      {/* ── ARCHIVE FACILITY CONFIRMATION MODAL ───────────────────────── */}
      {loanToArchive && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-in fade-in duration-150">
          <div className="bg-white border border-[#EEF1F5] w-full max-w-md rounded-2xl shadow-2xl p-6 space-y-5 animate-in zoom-in-95 duration-150">
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-amber-100 text-amber-700 flex items-center justify-center shrink-0">
                  <Archive className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-[#111827]">Archive credit facility?</h3>
                  <p className="text-xs text-[#6B7280]">Historical data preservation</p>
                </div>
              </div>
              <button
                onClick={() => setLoanToArchive(null)}
                className="p-1 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="bg-amber-50/80 border border-amber-200/80 rounded-xl p-4 space-y-2 text-xs text-amber-900">
              <p className="font-semibold">
                You are archiving facility <strong className="text-amber-950 font-mono">#{loanToArchive.id.slice(0, 8)}</strong> (
                {formatCurrency(loanToArchive.principal_amount?.amount, loanToArchive.principal_amount?.currency)}).
              </p>
              <p className="text-amber-800">
                This will remove the facility from your active portfolio while preserving its historical agreements, documents, and monitoring results.
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
                onClick={() => setLoanToArchive(null)}
                disabled={archiveLoading}
                className="flex-1 py-2.5 border border-[#EEF1F5] rounded-xl text-xs font-semibold text-[#6B7280] hover:bg-gray-50 transition-colors disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleArchiveLoan}
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
                    <span>Archive Facility</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── RESTORE FACILITY CONFIRMATION MODAL ───────────────────────── */}
      {loanToRestore && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-in fade-in duration-150">
          <div className="bg-white border border-[#EEF1F5] w-full max-w-md rounded-2xl shadow-2xl p-6 space-y-5 animate-in zoom-in-95 duration-150">
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-emerald-100 text-emerald-700 flex items-center justify-center shrink-0">
                  <RotateCcw className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-[#111827]">Restore credit facility?</h3>
                  <p className="text-xs text-[#6B7280]">Return to active portfolio</p>
                </div>
              </div>
              <button
                onClick={() => setLoanToRestore(null)}
                className="p-1 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="bg-emerald-50/80 border border-emerald-200/80 rounded-xl p-4 space-y-2 text-xs text-emerald-900">
              <p className="font-semibold">
                You are restoring facility <strong className="text-emerald-950 font-mono">#{loanToRestore.id.slice(0, 8)}</strong> (
                {formatCurrency(loanToRestore.principal_amount?.amount, loanToRestore.principal_amount?.currency)}).
              </p>
              <p className="text-emerald-800">
                This will return the facility to active portfolio monitoring.
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
                onClick={() => setLoanToRestore(null)}
                disabled={restoreLoading}
                className="flex-1 py-2.5 border border-[#EEF1F5] rounded-xl text-xs font-semibold text-[#6B7280] hover:bg-gray-50 transition-colors disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleRestoreLoan}
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
                    <span>Restore Facility</span>
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
