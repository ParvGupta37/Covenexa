import { useState, useEffect } from "react";
import { X, Plus, Loader2 } from "lucide-react";
import api from "@/lib/api";
import { useCompanyStore } from "@/store/company.store";

interface CreateFacilityModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: (createdLoanId: string) => void;
  defaultBorrowerId?: string;
}

export function CreateFacilityModal({
  isOpen,
  onClose,
  onSuccess,
  defaultBorrowerId,
}: CreateFacilityModalProps) {
  const { companies, selectedCompanyId } = useCompanyStore();

  const todayStr = new Date().toISOString().split("T")[0];
  const fiveYearsStr = new Date(Date.now() + 5 * 365 * 86400 * 1000).toISOString().split("T")[0];

  const [borrowerId, setBorrowerId] = useState(defaultBorrowerId || selectedCompanyId || "");
  const [amount, setAmount] = useState<number>(50000000);
  const [currency, setCurrency] = useState("USD");
  const [interestRatePct, setInterestRatePct] = useState<number>(6.5);
  const [startDate, setStartDate] = useState(todayStr);
  const [maturityDate, setMaturityDate] = useState(fiveYearsStr);
  const [submitting, setSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");

  useEffect(() => {
    if (defaultBorrowerId || selectedCompanyId) {
      setBorrowerId(defaultBorrowerId || selectedCompanyId || "");
    }
  }, [defaultBorrowerId, selectedCompanyId]);

  if (!isOpen) return null;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErrorMsg("");

    if (!borrowerId) {
      setErrorMsg("Please select a target borrower entity.");
      return;
    }
    if (amount <= 0) {
      setErrorMsg("Principal amount must be greater than zero.");
      return;
    }
    if (interestRatePct <= 0 || interestRatePct > 100) {
      setErrorMsg("Interest rate percentage must be between 0 and 100.");
      return;
    }

    setSubmitting(true);
    try {
      const res = await api.post("/api/v1/loans/", {
        borrower_id: borrowerId,
        principal_amount: {
          amount: Number(amount),
          currency: currency,
        },
        interest_rate: Number(interestRatePct) / 100.0,
        start_date: startDate,
        maturity_date: maturityDate,
        status: "ACTIVE",
      });

      const createdId = res.data?.id;
      onClose();
      if (onSuccess && createdId) {
        onSuccess(createdId);
      }
    } catch (err: any) {
      console.error("Failed to create facility", err);
      setErrorMsg(err.response?.data?.detail || "Failed to create loan facility.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-card border border-border rounded-2xl p-6 max-w-lg w-full shadow-2xl space-y-6 animate-in fade-in zoom-in-95 duration-200">
        <div className="flex items-center justify-between border-b border-border pb-4">
          <div>
            <h3 className="font-bold text-lg text-foreground">Create Credit Loan Facility</h3>
            <p className="text-xs text-muted-foreground mt-0.5">Register a new credit facility for monitoring</p>
          </div>
          <button
            onClick={onClose}
            className="p-1 text-muted-foreground hover:text-foreground rounded-lg hover:bg-muted transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4 text-sm">
          {/* Target Borrower */}
          <div className="space-y-1.5">
            <label className="font-semibold text-foreground text-xs">Target Borrower Entity *</label>
            <select
              value={borrowerId}
              onChange={(e) => setBorrowerId(e.target.value)}
              required
              className="w-full bg-background border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-primary"
            >
              <option value="" disabled>Select borrower...</option>
              {companies.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.company_name} ({c.sector})
                </option>
              ))}
            </select>
          </div>

          {/* Principal Amount & Currency */}
          <div className="grid grid-cols-3 gap-3">
            <div className="col-span-2 space-y-1.5">
              <label className="font-semibold text-foreground text-xs">Facility Principal Amount *</label>
              <input
                type="number"
                min="1"
                step="10000"
                value={amount}
                onChange={(e) => setAmount(Number(e.target.value))}
                required
                className="w-full bg-background border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-primary"
              />
            </div>
            <div className="space-y-1.5">
              <label className="font-semibold text-foreground text-xs">Currency</label>
              <select
                value={currency}
                onChange={(e) => setCurrency(e.target.value)}
                className="w-full bg-background border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-primary"
              >
                <option value="USD">USD ($)</option>
                <option value="EUR">EUR (€)</option>
                <option value="GBP">GBP (£)</option>
              </select>
            </div>
          </div>

          {/* Interest Rate */}
          <div className="space-y-1.5">
            <label className="font-semibold text-foreground text-xs">Interest Rate (%) *</label>
            <input
              type="number"
              min="0.1"
              max="50"
              step="0.05"
              value={interestRatePct}
              onChange={(e) => setInterestRatePct(Number(e.target.value))}
              required
              placeholder="e.g. 6.5"
              className="w-full bg-background border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-primary"
            />
          </div>

          {/* Dates */}
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <label className="font-semibold text-foreground text-xs">Origination Date *</label>
              <input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                required
                className="w-full bg-background border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-primary"
              />
            </div>
            <div className="space-y-1.5">
              <label className="font-semibold text-foreground text-xs">Maturity Date *</label>
              <input
                type="date"
                value={maturityDate}
                onChange={(e) => setMaturityDate(e.target.value)}
                required
                className="w-full bg-background border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-primary"
              />
            </div>
          </div>

          {errorMsg && (
            <div className="p-3 bg-red-500/10 border border-red-500/20 text-red-400 rounded-lg text-xs font-semibold">
              {errorMsg}
            </div>
          )}

          <div className="pt-2 flex justify-end gap-3 border-t border-border">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 bg-muted text-muted-foreground hover:text-foreground rounded-lg font-semibold text-sm transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="px-5 py-2 bg-primary text-primary-foreground font-semibold rounded-lg text-sm hover:bg-primary/90 transition-all flex items-center gap-2 disabled:opacity-50"
            >
              {submitting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
              Register Facility
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
