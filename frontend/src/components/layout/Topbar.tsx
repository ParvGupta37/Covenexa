import { useEffect, useState } from "react";
import { Bell, Search, Building2, Users, Plus, ChevronDown } from "lucide-react";
import { useCompanyStore } from "@/store/company.store";
import { useAuthStore } from "@/store/auth.store";
import api from "@/lib/api";

export function Topbar() {
  const { user } = useAuthStore();
  const {
    companies,
    selectedCompanyId,
    fetchCompanies,
    setSelectedCompanyId,
    openRegisterModal,
  } = useCompanyStore();

  const [orgName, setOrgName] = useState<string>("");

  useEffect(() => {
    fetchCompanies();
  }, [fetchCompanies]);

  // Fetch the lender organization name for the top context strip
  useEffect(() => {
    api.get("/api/v1/organizations/")
      .then((res) => {
        if (res.data && res.data.length > 0) setOrgName(res.data[0].name);
      })
      .catch(() => {});
  }, []);

  return (
    <header className="h-16 bg-white border-b border-[#EEF1F5] px-8 flex items-center justify-between gap-4 shrink-0">
      {/* Left: Search + Context Selectors */}
      <div className="flex items-center gap-4 flex-1">
        {/* Global Search */}
        <div className="relative w-72 max-w-sm">
          <Search className="absolute left-3.5 top-2.5 w-4 h-4 text-[#9CA3AF]" />
          <input
            type="text"
            placeholder="Search borrowers, loans, covenants..."
            className="w-full bg-[#F8F9FC] border border-[#EEF1F5] rounded-full pl-10 pr-4 py-2 text-xs font-medium text-[#111827] focus:outline-none focus:ring-2 focus:ring-[#7C8DFB]/50 transition-all placeholder:text-[#9CA3AF]"
          />
        </div>

        {/* Organization context pill — shows the lender/fund name */}
        {orgName && (
          <div className="hidden md:flex items-center gap-2 bg-[#F0FDF4] border border-[#BBF7D0] rounded-full px-3 py-1.5">
            <Building2 className="w-3.5 h-3.5 text-[#16A34A]" />
            <span className="text-[10px] font-semibold text-[#16A34A] uppercase tracking-wide">Org:</span>
            <span className="text-xs font-bold text-[#166534] max-w-[140px] truncate">{orgName}</span>
          </div>
        )}

        {/* Borrower (Portfolio Company) Switcher */}
        <div className="hidden md:flex items-center gap-2 bg-[#F8F9FC] border border-[#EEF1F5] rounded-full px-3 py-1.5">
          <Users className="w-3.5 h-3.5 text-[#7C8DFB]" />
          <span className="text-[10px] font-medium text-[#9CA3AF] uppercase tracking-wide">Borrower:</span>
          {companies.length === 0 ? (
            <button
              onClick={openRegisterModal}
              className="text-xs font-semibold text-[#7C8DFB] hover:text-[#4F46E5] transition-colors"
            >
              + Add first borrower
            </button>
          ) : (
            <>
              <select
                value={selectedCompanyId}
                onChange={(e) => setSelectedCompanyId(e.target.value)}
                className="bg-transparent text-xs font-semibold text-[#111827] focus:outline-none cursor-pointer pr-1 max-w-[150px]"
              >
                {companies.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.company_name}
                  </option>
                ))}
              </select>
              <ChevronDown className="w-3 h-3 text-[#9CA3AF]" />
            </>
          )}
        </div>

        {/* Add Borrower quick button */}
        {companies.length > 0 && (
          <button
            onClick={openRegisterModal}
            className="hidden lg:flex items-center gap-1 px-3 py-1.5 text-xs font-semibold text-[#7C8DFB] hover:bg-[#E8ECFF] rounded-full transition-all"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Add Borrower</span>
          </button>
        )}
      </div>

      {/* Right: Notifications + User Profile */}
      <div className="flex items-center gap-3">
        <button className="relative w-9 h-9 rounded-full bg-[#F8F9FC] hover:bg-[#E8ECFF] flex items-center justify-center text-[#6B7280] transition-colors">
          <Bell className="w-4 h-4" />
          <span className="absolute top-2 right-2 w-2 h-2 bg-[#EF4444] rounded-full ring-2 ring-white" />
        </button>

        <div className="flex items-center gap-2.5 pl-2 border-l border-[#EEF1F5]">
          <div className="w-8 h-8 rounded-full bg-[#E8ECFF] text-[#4F46E5] font-bold text-xs flex items-center justify-center shrink-0">
            {user?.name ? user.name.charAt(0).toUpperCase() : "A"}
          </div>
          <div className="hidden sm:block text-left">
            <p className="text-xs font-bold text-[#111827]">
              {user?.name || "Analyst"}
            </p>
            <p className="text-[10px] text-[#6B7280] capitalize">
              {user?.role ? user.role.toLowerCase() : "Credit Officer"}
            </p>
          </div>
        </div>
      </div>
    </header>
  );
}
