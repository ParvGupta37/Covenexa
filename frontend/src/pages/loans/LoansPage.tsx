import { useState, useEffect } from "react";
import { ShieldAlert, Plus, Coins, Percent, Calendar } from "lucide-react";
import api from "@/lib/api";
import { Loan } from "@/types";

export default function LoansPage() {
  const [loans, setLoans] = useState<Loan[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadLoans() {
      try {
        const res = await api.get("/api/v1/loans/");
        setLoans(res.data);
      } catch (err) {
        console.error("Failed to load loans", err);
      } finally {
        setLoading(false);
      }
    }
    loadLoans();
  }, []);

  return (
    <div className="space-y-8">
      {/* Title Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Active Loans & Covenants</h1>
          <p className="text-muted-foreground mt-1">Monitor credit facilities, interest rates, and compliance parameters.</p>
        </div>
        <button className="flex items-center gap-2 bg-primary hover:bg-primary/90 text-primary-foreground font-semibold px-4 py-2.5 rounded-lg text-sm transition-all shadow-sm">
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
              Register a new loan facility tied to a borrower to start monitoring covenants.
            </p>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {loans.map((loan) => (
            <div key={loan.id} className="bg-card border border-border rounded-xl p-6 space-y-6 shadow-sm hover:border-primary/40 transition-all">
              <div className="flex justify-between items-center">
                <div className="space-y-1">
                  <span className="text-xs text-muted-foreground uppercase tracking-widest font-mono">Facility ID: {loan.id.slice(0, 8)}</span>
                  <p className="text-2xl font-bold">
                    {loan.principal_amount.currency} {loan.principal_amount.amount.toLocaleString()}
                  </p>
                </div>
                <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
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
                <span>Agreement File: {loan.agreement_id.slice(0, 8)}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
