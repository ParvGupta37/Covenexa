import { Bell, Search, Sparkles } from "lucide-react";

export function Topbar() {
  return (
    <header className="h-16 border-b border-border bg-card px-8 flex items-center justify-between shadow-sm">
      {/* Search Bar */}
      <div className="relative w-96">
        <Search className="absolute left-3 top-2.5 w-4 h-4 text-muted-foreground" />
        <input
          type="text"
          placeholder="Search Borrowers, Covenants, or Loans..."
          className="w-full bg-background border border-border rounded-lg pl-10 pr-4 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-primary focus:border-primary transition-all placeholder:text-muted-foreground/60"
        />
      </div>

      {/* Action triggers */}
      <div className="flex items-center gap-4">
        {/* System alerts notifications */}
        <button className="relative p-2 rounded-lg hover:bg-accent text-muted-foreground hover:text-foreground transition-all">
          <Bell className="w-5 h-5" />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-destructive rounded-full"></span>
        </button>

        {/* AI copilot quick reference button */}
        <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-primary/10 text-primary border border-primary/20 text-xs font-semibold animate-pulse">
          <Sparkles className="w-3.5 h-3.5" />
          System Online
        </div>
      </div>
    </header>
  );
}
