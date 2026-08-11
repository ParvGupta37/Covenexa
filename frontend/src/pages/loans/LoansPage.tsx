import { useState, useEffect } from "react";
import { ShieldAlert, Plus, Coins, Percent, Calendar, Building2 } from "lucide-react";
import api from "@/lib/api";
import { Loan } from "@/types";
import { useCompanyStore } from "@/store/company.store";
import { CreateFacilityModal } from "@/components/loans/CreateFacilityModal";

export default function LoansPage() {
  const { companies, selectedCompanyId, selectedCompany, fetchCompanies } = useCompanyStore();

  const [loans, setLoans] = useState<Loan[]>([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);

  useEffect(() => {
    fetchCompanies();
  }, [fetchCompanies]);

  async function loadLoans() {
    setLoading(true);
    try {
      const url = selectedCompanyId ? `/api/v1/loans/?borrower_id=${selectedCompanyId}` : "/api/v1/loans/";
      const res = await api.get(url);
      setLoans(res.data || []);
    } catch (err) {
      console.error("Failed to load loans", err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadLoans();
  }, [selectedCompanyId]);

  return (
    <div className="space-y-8">
      {/* Title Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Active Loans & Credit Facilities</h1>
          <p className="text-muted-foreground mt-1">
            Monitor credit facilities, interest rates, and compliance parameters for{" "}
            <strong className="text-foreground">{selectedCompany?.company_name || "portfolio entities"}</strong>.
          </p>
        </div>
        <button
          onClick={() => setIsModalOpen(true)}
          className="flex items-center gap-2 bg-primary hover:bg-primary/90 text-primary-foreground font-semibold px-4 py-2.5 rounded-lg text-sm transition-all shadow-sm shrink-0"
        >
          <Plus className="w-4 h-4" />
          Create Facility
        </button>
      </div>

      {/* Facility listings grid */}
      {loading ? (
        <div className="flex flex-col items-center justify-center py-20 space-y-3">
          <div className="w-10 h-10 border-4 border-primary border-t-transparent rounded-full animate-spin"></div>
          <p className="text-muted-foreground text-sm">Querying database facilities...</p>
        </div>
      ) : loans.length === 0 ? (
        <div className="border border-dashed border-border rounded-xl p-12 text-center space-y-4">
          <div className="inline-flex p-4 bg-muted rounded-full text-muted-foreground">
            <Coins className="w-8 h-8" />
          </div>
          <div className="space-y-1">
            <h4 className="font-bold text-lg">No Active Facilities Found</h4>
            <p className="text-muted-foreground text-sm max-w-sm mx-auto">
              Register a new loan facility tied to {selectedCompany?.company_name || "a borrower"} to start monitoring covenants.
            </p>
          </div>
          <button
            onClick={() => setIsModalOpen(true)}
            className="inline-flex items-center gap-2 bg-primary text-primary-foreground px-4 py-2 rounded-lg text-sm font-semibold hover:bg-primary/90 transition-all"
          >
            <Plus className="w-4 h-4" /> Create Facility Now
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {loans.map((loan) => {
            const borrowerName = companies.find((c) => c.id === loan.borrower_id)?.company_name || "Borrower Entity";
            return (
              <div key={loan.id} className="bg-card border border-border rounded-xl p-6 space-y-6 shadow-sm hover:border-primary/40 transition-all">
                <div className="flex justify-between items-start">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-muted-foreground uppercase tracking-widest font-mono">Facility #{loan.id.slice(0, 8)}</span>
                      <span className="text-xs font-semibold text-primary px-2 py-0.5 bg-primary/10 border border-primary/20 rounded-full flex items-center gap-1">
                        <Building2 className="w-3 h-3" /> {borrowerName}
                      </span>
                    </div>
                    <p className="text-2xl font-bold">
                      {/* MEDIUM-2: null amount → "N/A", not $0.
                          Currency "USD" fallback is legitimate (Money VO enforces USD). */}
                      {loan.principal_amount?.currency || "USD"}{" "}
                      {loan.principal_amount?.amount != null
                        ? Number(loan.principal_amount.amount).toLocaleString()
                        : "N/A"}
                    </p>
                  </div>
                  <span className={`px-2.5 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
                    loan.status === "ACTIVE" 
                      ? "bg-emerald-500/15 text-emerald-500" 
                      : "bg-destructive/15 text-destructive"
                  }`}>
                    {loan.status}
                  </span>
                </div>

                {/* Grid properties */}
                <div className="grid grid-cols-3 gap-4 py-4 border-t border-b border-border text-sm">
                  <div className="space-y-1">
                    <div className="flex items-center gap-1.5 text-muted-foreground text-xs uppercase tracking-wider">
                      <Percent className="w-3.5 h-3.5" />
                      <span>Rate</span>
                    </div>
                    <span className="font-semibold">{(loan.interest_rate * 100).toFixed(2)}%</span>
                  </div>
                  <div className="space-y-1">
                    <div className="flex items-center gap-1.5 text-muted-foreground text-xs uppercase tracking-wider">
                      <Calendar className="w-3.5 h-3.5" />
                      <span>Origination</span>
                    </div>
                    <span className="font-semibold">{loan.start_date}</span>
                  </div>
                  <div className="space-y-1">
                    <div className="flex items-center gap-1.5 text-muted-foreground text-xs uppercase tracking-wider">
                      <Calendar className="w-3.5 h-3.5" />
                      <span>Maturity</span>
                    </div>
                    <span className="font-semibold">{loan.maturity_date}</span>
                  </div>
                </div>

                {/* Downstream references indicator */}
                <div className="flex items-center gap-2 text-xs text-primary font-semibold">
                  <ShieldAlert className="w-4 h-4" />
                  <span>
                    Agreement Document: {loan.agreement_id ? loan.agreement_id.slice(0, 8) : "Pending Ingestion"}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Create Facility Modal */}
      <CreateFacilityModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSuccess={() => loadLoans()}
      />
    </div>
  );
}
