import { useState, useEffect } from "react";
import { Users, Plus, ShieldAlert } from "lucide-react";
import api from "@/lib/api";
import { Borrower } from "@/types";

export default function BorrowersPage() {
  const [borrowers, setBorrowers] = useState<Borrower[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadBorrowers() {
      try {
        const res = await api.get("/api/v1/borrowers/");
        setBorrowers(res.data);
      } catch (err) {
        console.error("Failed to load borrowers", err);
      } finally {
        setLoading(false);
      }
    }
    loadBorrowers();
  }, []);

  return (
    <div className="space-y-8">
      {/* Title Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Portfolio Borrowers</h1>
          <p className="text-muted-foreground mt-1">Manage credit ratings and profiles of borrowers.</p>
        </div>
        <button className="flex items-center gap-2 bg-primary hover:bg-primary/90 text-primary-foreground font-semibold px-4 py-2.5 rounded-lg text-sm transition-all shadow-sm">
          <Plus className="w-4 h-4" />
          Add Borrower
        </button>
      </div>

      {/* Borrowers Directory Grid */}
      {loading ? (
        <div className="flex flex-col items-center justify-center py-20 space-y-3">
          <div className="w-10 h-10 border-4 border-primary border-t-transparent rounded-full animate-spin"></div>
          <p className="text-muted-foreground text-sm">Querying Database...</p>
        </div>
      ) : borrowers.length === 0 ? (
        <div className="border border-dashed border-border rounded-xl p-12 text-center space-y-4">
          <div className="inline-flex p-4 bg-muted rounded-full text-muted-foreground">
            <Users className="w-8 h-8" />
          </div>
          <div className="space-y-1">
            <h4 className="font-bold text-lg">No Borrowers Found</h4>
            <p className="text-muted-foreground text-sm max-w-sm mx-auto">
              Get started by registering a new borrower profile using the administrative action link.
            </p>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {borrowers.map((borrower) => (
            <div key={borrower.id} className="bg-card border border-border rounded-xl p-6 space-y-6 shadow-sm hover:border-primary/40 transition-all">
              <div className="flex justify-between items-start">
                <div className="space-y-1">
                  <h3 className="font-bold text-lg">{borrower.company_name}</h3>
                  <p className="text-xs text-muted-foreground">{borrower.sector} • {borrower.country}</p>
                </div>
                <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
                  borrower.risk_rating.level === "CRITICAL" || borrower.risk_rating.level === "HIGH"
                    ? "bg-destructive/15 text-destructive"
                    : borrower.risk_rating.level === "MEDIUM"
                    ? "bg-amber-500/15 text-amber-500"
                    : "bg-emerald-500/15 text-emerald-500"
                }`}>
                  Risk: {borrower.risk_rating.level}
                </span>
              </div>

              {/* Score indicator */}
              <div className="pt-2 border-t border-border flex justify-between items-center text-sm">
                <div className="flex items-center gap-1.5 text-muted-foreground">
                  <ShieldAlert className="w-4 h-4" />
                  <span>Risk Score</span>
                </div>
                <span className="font-bold">{borrower.risk_rating.score} / 10</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
