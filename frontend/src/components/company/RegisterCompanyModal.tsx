import { useState, useEffect } from "react";
import { Building2, X, Loader2, PlusCircle, AlertTriangle } from "lucide-react";
import { useCompanyStore } from "@/store/company.store";
import api from "@/lib/api";

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

  // Org creation state
  const [hasOrg, setHasOrg] = useState<boolean | null>(null); // null = checking
  const [needsOrg, setNeedsOrg] = useState(false);
  const [orgName, setOrgName] = useState("");
  const [orgIndustry, setOrgIndustry] = useState("Private Credit");
  const [orgLoading, setOrgLoading] = useState(false);

  // Check if any org exists when modal opens
  useEffect(() => {
    if (!isRegisterModalOpen) return;
    setHasOrg(null);
    setNeedsOrg(false);
    setError("");
    api.get("/api/v1/organizations/").then((res) => {
      setHasOrg(res.data && res.data.length > 0);
    }).catch(() => setHasOrg(false));
  }, [isRegisterModalOpen]);

  if (!isRegisterModalOpen) return null;

  const handleCreateOrg = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    if (!orgName.trim()) { setError("Please enter an organization name."); return; }
    setOrgLoading(true);
    try {
      await api.post("/api/v1/organizations/", { name: orgName.trim(), industry: orgIndustry });
      setHasOrg(true);
      setNeedsOrg(false);
    } catch (err: any) {
      const detail = err?.response?.data?.detail;
      setError(typeof detail === "string" ? detail : "Failed to create organization.");
    } finally {
      setOrgLoading(false);
    }
  };

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
      // Handle both axios errors (err.response.data.detail) and plain errors (err.message)
      const axiosDetail = err?.response?.data?.detail;
      const plainMsg = err?.message;
      const msg =
        typeof axiosDetail === "string"
          ? axiosDetail
          : Array.isArray(axiosDetail)
          ? axiosDetail.map((d: any) => d.msg).join(", ")
          : typeof plainMsg === "string" && plainMsg.length > 0
          ? plainMsg
          : "Registration failed. Please try again.";
      setError(msg);
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
          <div className="p-3 bg-red-500/10 border border-red-500/20 text-red-400 text-sm rounded-xl flex items-start gap-2">
            <AlertTriangle className="w-4 h-4 mt-0.5 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Checking orgs */}
        {hasOrg === null && (
          <div className="flex items-center justify-center py-6 gap-2 text-muted-foreground text-sm">
            <Loader2 className="w-4 h-4 animate-spin" />
            Checking organization...
          </div>
        )}

        {/* No org found — show inline org creation */}
        {hasOrg === false && !needsOrg && (
          <div className="p-4 bg-amber-500/10 border border-amber-500/20 rounded-xl space-y-3">
            <div className="flex items-start gap-2 text-amber-400">
              <AlertTriangle className="w-4 h-4 mt-0.5 shrink-0" />
              <div>
                <p className="text-sm font-semibold">No organization found</p>
                <p className="text-xs text-amber-400/80 mt-0.5">
                  You need to create an organization (your fund or firm) before registering borrowers.
                </p>
              </div>
            </div>
            <button
              onClick={() => { setNeedsOrg(true); setError(""); }}
              className="w-full py-2 bg-amber-500/20 hover:bg-amber-500/30 text-amber-300 text-sm font-semibold rounded-lg transition-colors border border-amber-500/30"
            >
              + Create Organization First
            </button>
          </div>
        )}

        {/* Inline org creation form */}
        {hasOrg === false && needsOrg && (
          <form onSubmit={handleCreateOrg} className="space-y-4">
            <p className="text-sm font-semibold text-foreground">Step 1 — Create Your Organization</p>
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                Organization Name *
              </label>
              <input
                type="text"
                value={orgName}
                onChange={(e) => setOrgName(e.target.value)}
                placeholder="e.g. Covenexa Capital, Acme Credit Fund"
                className="w-full bg-background border border-border rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-1 focus:ring-primary"
                required
              />
            </div>
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                Industry
              </label>
              <select
                value={orgIndustry}
                onChange={(e) => setOrgIndustry(e.target.value)}
                className="w-full bg-background border border-border rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:ring-1 focus:ring-primary"
              >
                {["Private Credit", "Direct Lending", "Asset Management", "Investment Banking",
                  "Technology", "Healthcare", "Real Estate", "Energy", "Other"].map((s) => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
            </div>
            <div className="flex gap-3 pt-2">
              <button
                type="button"
                onClick={() => setNeedsOrg(false)}
                className="flex-1 py-2.5 border border-border rounded-xl text-sm font-semibold hover:bg-muted/50 transition-colors"
              >
                Back
              </button>
              <button
                type="submit"
                disabled={orgLoading || !orgName.trim()}
                className="flex-1 py-2.5 bg-primary text-primary-foreground text-sm font-semibold rounded-xl hover:bg-primary/90 transition-all disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {orgLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <PlusCircle className="w-4 h-4" />}
                Create Organization
              </button>
            </div>
          </form>
        )}

        {/* Main borrower registration form — shown once org exists */}
        {hasOrg === true && (
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
        )}
      </div>
    </div>
  );
}
