import { useEffect } from "react";
import { Bell, Search, Sparkles, Building2, PlusCircle, ChevronDown } from "lucide-react";
import { useCompanyStore } from "@/store/company.store";

export function Topbar() {
  const {
    companies,
    selectedCompanyId,
    selectedCompany,
    fetchCompanies,
    setSelectedCompanyId,
    openRegisterModal,
  } = useCompanyStore();

  useEffect(() => {
    fetchCompanies();
  }, []);

  return (
    <header className="h-16 border-b border-border bg-card px-6 flex items-center justify-between shadow-sm gap-4">
      {/* Search Bar */}
      <div className="relative w-80 flex-shrink-0">
        <Search className="absolute left-3 top-2.5 w-4 h-4 text-muted-foreground" />
        <input
          type="text"
          placeholder="Search Borrowers, Covenants, or Loans..."
          className="w-full bg-background border border-border rounded-lg pl-10 pr-4 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-primary focus:border-primary transition-all placeholder:text-muted-foreground/60"
        />
      </div>

      {/* ── Company Switcher Bar ─────────────────────────────────────── */}
      <div className="flex items-center gap-2 flex-1 justify-center">
        {/* Company Selector Dropdown */}
        <div className="flex items-center gap-2 bg-background border border-border rounded-xl px-3 py-2 min-w-[220px] max-w-xs">
          <Building2 className="w-4 h-4 text-primary flex-shrink-0" />
          <select
            value={selectedCompanyId}
            onChange={(e) => setSelectedCompanyId(e.target.value)}
            className="bg-transparent text-sm font-semibold text-foreground focus:outline-none flex-1 cursor-pointer"
          >
            {companies.length === 0 ? (
              <option value="">No companies yet</option>
            ) : (
              companies.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.company_name}
                </option>
              ))
            )}
          </select>
          <ChevronDown className="w-3.5 h-3.5 text-muted-foreground flex-shrink-0" />
        </div>

        {selectedCompany && (
          <span className="text-xs text-muted-foreground hidden md:block px-2 py-1 rounded-full bg-muted/40 border border-border">
            {selectedCompany.sector} · {selectedCompany.country}
          </span>
        )}

        {/* Register New Company Button */}
        <button
          onClick={openRegisterModal}
          className="flex items-center gap-1.5 px-3 py-2 bg-primary/10 text-primary border border-primary/30 hover:bg-primary/20 transition-all rounded-xl text-xs font-semibold"
        >
          <PlusCircle className="w-3.5 h-3.5" />
          Register Company
        </button>
      </div>

      {/* Right Actions */}
      <div className="flex items-center gap-3 flex-shrink-0">
        <button className="relative p-2 rounded-lg hover:bg-accent text-muted-foreground hover:text-foreground transition-all">
          <Bell className="w-5 h-5" />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-destructive rounded-full" />
        </button>

        <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-primary/10 text-primary border border-primary/20 text-xs font-semibold animate-pulse">
          <Sparkles className="w-3.5 h-3.5" />
          System Online
        </div>
      </div>
    </header>
  );
}
