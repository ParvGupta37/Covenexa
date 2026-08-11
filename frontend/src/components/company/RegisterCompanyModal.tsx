import { useState } from "react";
import { Building2, X, Loader2, PlusCircle } from "lucide-react";
import { useCompanyStore } from "@/store/company.store";

const RISK_OPTIONS: { label: string; level: string; score: number }[] = [
  { label: "AAA — Prime (Lowest Risk)", level: "LOW", score: 1 },
  { label: "AA+  — High Grade",          level: "LOW", score: 2 },
  { label: "A+   — Upper Medium",        level: "LOW", score: 3 },
  { label: "BBB+ — Investment Grade",    level: "MEDIUM", score: 5 },
  { label: "BB   — Speculative",         level: "MEDIUM", score: 6 },
  { label: "B    — Highly Speculative",  level: "HIGH", score: 8 },
  { label: "CCC  — High Default Risk",   level: "HIGH", score: 10 },
];

export function RegisterCompanyModal() {
  const { isRegisterModalOpen, closeRegisterModal, registerCompany, loading } =
    useCompanyStore();

  const [companyName, setCompanyName] = useState("");
  const [sector, setSector] = useState("Technology");
  const [country, setCountry] = useState("USA");
  const [riskIdx, setRiskIdx] = useState(3); // BBB+ default
  const [error, setError] = useState("");

  if (!isRegisterModalOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    if (!companyName.trim()) {
      setError("Please enter a valid company name.");
      return;
    }
    const chosen = RISK_OPTIONS[riskIdx];
    try {
      await registerCompany({
        company_name: companyName.trim(),
        sector,
        country,
        risk_level: chosen.level,
        risk_score: chosen.score,
      });
      setCompanyName("");
      setRiskIdx(3);
    } catch (err: any) {
      const detail = err?.response?.data?.detail;
      setError(
        typeof detail === "string"
          ? detail
          : Array.isArray(detail)
          ? detail.map((d: any) => d.msg).join(", ")
          : "Registration failed. Please try again."
      );
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
      <div className="bg-card border border-border w-full max-w-lg rounded-2xl p-6 shadow-2xl space-y-5 animate-in fade-in zoom-in duration-200">
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-border">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-primary/20 text-primary rounded-xl border border-primary/30">
              <Building2 className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-foreground">Register New Company</h2>
              <p className="text-xs text-muted-foreground">
                Add a borrower entity to monitor financial risk & SEC filings
              </p>
            </div>
          </div>
          <button
            onClick={closeRegisterModal}
            className="p-1.5 text-muted-foreground hover:text-foreground rounded-lg hover:bg-muted/50 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {error && (
          <div className="p-3 bg-red-500/10 border border-red-500/20 text-red-400 text-sm rounded-xl">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Company Name */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              Company Name *
            </label>
            <input
              type="text"
              value={companyName}
              onChange={(e) => setCompanyName(e.target.value)}
              placeholder="e.g. Apple Inc., Microsoft Corp, Tesla Motors"
              className="w-full bg-background border border-border rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-1 focus:ring-primary"
              required
            />
          </div>

          {/* Sector & Country */}
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                Industry Sector
              </label>
              <select
                value={sector}
                onChange={(e) => setSector(e.target.value)}
                className="w-full bg-background border border-border rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:ring-1 focus:ring-primary"
              >
                {[
                  "Technology", "Transportation", "Healthcare",
                  "Energy", "Financials", "Consumer", "Manufacturing",
                  "Real Estate", "Telecommunications",
                ].map((s) => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                Country
              </label>
              <input
                type="text"
                value={country}
                onChange={(e) => setCountry(e.target.value)}
                className="w-full bg-background border border-border rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-1 focus:ring-primary"
                required
              />
            </div>
          </div>

          {/* Credit Risk Rating */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              Credit Risk Rating
            </label>
            <select
              value={riskIdx}
              onChange={(e) => setRiskIdx(Number(e.target.value))}
              className="w-full bg-background border border-border rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:ring-1 focus:ring-primary"
            >
              {RISK_OPTIONS.map((opt, idx) => (
                <option key={idx} value={idx}>{opt.label}</option>
              ))}
            </select>
          </div>

          <div className="pt-4 border-t border-border flex justify-end gap-3">
            <button
              type="button"
              onClick={closeRegisterModal}
              className="px-4 py-2.5 border border-border rounded-xl text-sm font-semibold hover:bg-muted/50 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading || !companyName.trim()}
              className="px-5 py-2.5 bg-primary text-primary-foreground text-sm font-semibold rounded-xl hover:bg-primary/90 transition-all disabled:opacity-50 flex items-center gap-2"
            >
              {loading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <PlusCircle className="w-4 h-4" />
              )}{" "}
              Register Entity
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
