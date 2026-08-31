import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import {
  LayoutDashboard,
  Users,
  ShieldAlert,
  Activity,
  FileStack,
  BrainCircuit,
  FileText,
  ArrowLeftToLine,
  ArrowRightToLine,
  LogOut,
  Sliders,
  Network,
  Settings2,
} from "lucide-react";
import { useAuthStore } from "@/store/auth.store";

export function Sidebar() {
  const { pathname } = useLocation();
  const navigate = useNavigate();
  const { logout, user } = useAuthStore();
  const [collapsed, setCollapsed] = useState(false);

  const navItems = [
    { label: "Overview", path: "/app", icon: LayoutDashboard, exact: true },
    { label: "Borrowers", path: "/app/borrowers", icon: Users },
    { label: "Loans", path: "/app/loans", icon: ShieldAlert },
    { label: "Risk Monitor", path: "/app/risk", icon: Activity },
    { label: "Stress Testing", path: "/app/stress", icon: Sliders },
    { label: "Knowledge Graph", path: "/app/graph", icon: Network },
    { label: "Documents", path: "/app/uploads", icon: FileStack },
    { label: "AI Copilot", path: "/app/copilot", icon: BrainCircuit },
    { label: "Reports & Audit", path: "/app/audit", icon: FileText },
  ];

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const isActive = (item: { path: string; exact?: boolean }) =>
    item.exact ? pathname === item.path : pathname.startsWith(item.path);

  return (
    <aside
      className={`${
        collapsed ? "w-20" : "w-64"
      } bg-white border-r border-[#EEF1F5] h-screen flex flex-col justify-between py-6 px-4 shrink-0 transition-all duration-300 z-20`}
    >
      <div className="space-y-6">
        {/* Logo & Brand Header */}
        <div className="flex items-center gap-3 px-2">
          <div className="w-9 h-9 rounded-xl bg-[#111827] flex items-center justify-center text-white shrink-0 shadow-sm">
            <svg
              className="w-5 h-5 text-white fill-current"
              viewBox="0 0 24 24"
            >
              <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
            </svg>
          </div>
          {!collapsed && (
            <span className="text-xl font-bold text-[#111827] tracking-tight">
              Covenexa
            </span>
          )}
        </div>

        {/* Navigation Section */}
        <nav className="space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const active = isActive(item);

            return (
              <Link
                key={item.path}
                to={item.path}
                title={collapsed ? item.label : undefined}
                className={`flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs font-semibold transition-all ${
                  active
                    ? "bg-[#E8ECFF] text-[#111827] shadow-sm"
                    : "text-[#6B7280] hover:bg-[#F8F9FC] hover:text-[#111827]"
                }`}
              >
                <Icon
                  className={`w-4 h-4 shrink-0 ${
                    active ? "text-[#4F46E5]" : "text-[#6B7280]"
                  }`}
                />
                {!collapsed && <span>{item.label}</span>}
              </Link>
            );
          })}
        </nav>
      </div>

      {/* Footer Section */}
      <div className="space-y-3 pt-4 border-t border-[#EEF1F5]">
        {/* Organization Settings — Admin only */}
        {user?.role === "ADMIN" && (
          <Link
            to="/app/settings/organization"
            title={collapsed ? "Organization Settings" : undefined}
            className={`flex items-center gap-3 px-3.5 py-2 rounded-xl text-xs font-semibold transition-colors ${
              pathname.startsWith("/app/settings")
                ? "bg-[#E8ECFF] text-[#111827]"
                : "text-[#6B7280] hover:bg-[#F8F9FC] hover:text-[#111827]"
            }`}
          >
            <Settings2 className="w-4 h-4 shrink-0 text-[#6B7280]" />
            {!collapsed && <span>Settings</span>}
          </Link>
        )}

        <button
          onClick={() => setCollapsed(!collapsed)}
          className="w-full flex items-center gap-3 px-3.5 py-2 rounded-xl text-xs font-semibold text-[#6B7280] hover:bg-[#F8F9FC] transition-colors"
        >
          {collapsed ? (
            <ArrowRightToLine className="w-4 h-4 shrink-0" />
          ) : (
            <>
              <ArrowLeftToLine className="w-4 h-4 shrink-0" />
              <span>Collapse</span>
            </>
          )}
        </button>

        {user && !collapsed && (
          <div className="px-3.5 py-2 bg-[#F8F9FC] rounded-xl flex items-center justify-between">
            <div className="min-w-0 flex-1 pr-2">
              <p className="text-xs font-bold text-[#111827] truncate">
                {user.name}
              </p>
              <p className="text-[11px] text-[#6B7280] truncate">{user.role}</p>
            </div>
            <button
              onClick={handleLogout}
              title="Sign Out"
              className="text-[#6B7280] hover:text-[#EF4444] p-1 transition-colors"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>
    </aside>
  );
}
