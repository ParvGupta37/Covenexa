import { Outlet } from "react-router-dom";
import { Sidebar } from "./Sidebar";
import { Topbar } from "./Topbar";

export function AppShell() {
  return (
    <div className="flex h-screen overflow-hidden bg-background">
      {/* Navigation sidebar */}
      <Sidebar />

      {/* Main viewport */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header toolbar */}
        <Topbar />

        {/* Content canvas scrolling */}
        <main className="flex-1 overflow-y-auto px-8 py-8">
          <div className="max-w-7xl mx-auto space-y-8">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
