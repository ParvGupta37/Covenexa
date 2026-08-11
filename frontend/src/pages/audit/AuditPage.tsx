import { useState, useEffect } from "react";
import {
  History, Activity,
  Filter, RefreshCw, Search
} from "lucide-react";
import api from "@/lib/api";

interface AuditItem {
  id: string;
  user_id?: string;
  user_email?: string;
  action: string;
  resource_type: string;
  resource_id?: string;
  details?: string;
  ip_address?: string;
  created_at: string;
}

const ACTION_COLORS: Record<string, { bg: string; text: string; label: string }> = {
  user_login:            { bg: "bg-blue-500/10 border-blue-500/20", text: "text-blue-400", label: "User Login" },
  borrower_created:      { bg: "bg-emerald-500/10 border-emerald-500/20", text: "text-emerald-400", label: "Entity Registered" },
  document_uploaded:     { bg: "bg-indigo-500/10 border-indigo-500/20", text: "text-indigo-400", label: "Document Uploaded" },
  sec_filing_submitted:  { bg: "bg-purple-500/10 border-purple-500/20", text: "text-purple-400", label: "SEC Filing Ingested" },
  risk_pipeline_executed:{ bg: "bg-amber-500/10 border-amber-500/20", text: "text-amber-400", label: "Risk Pipeline Run" },
  credit_memo_generated: { bg: "bg-teal-500/10 border-teal-500/20", text: "text-teal-400", label: "Credit Memo Export" },
};

export default function AuditPage() {
  const [logs, setLogs] = useState<AuditItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterAction, setFilterAction] = useState("");
  const [searchQuery, setSearchQuery] = useState("");

  useEffect(() => {
    fetchLogs();
  }, [filterAction]);

  async function fetchLogs() {
    setLoading(true);
    try {
      const url = filterAction
        ? `/api/v1/audit/?action=${filterAction}`
        : "/api/v1/audit/?limit=100";
      const res = await api.get(url);
      setLogs(res.data || []);
    } catch (e) {
      console.error("Failed to load audit logs", e);
    } finally {
      setLoading(false);
    }
  }

  const filteredLogs = logs.filter((log) => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    return (
      log.user_email?.toLowerCase().includes(q) ||
      log.action.toLowerCase().includes(q) ||
      log.resource_type.toLowerCase().includes(q) ||
      log.details?.toLowerCase().includes(q)
    );
  });

  return (
    <div className="space-y-8">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Enterprise Audit & Activity Logs</h1>
          <p className="text-muted-foreground mt-1">
            Complete immutable audit trail of user actions, AI pipeline executions, and risk intelligence events
          </p>
        </div>

        <button
          onClick={fetchLogs}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 bg-card border border-border text-foreground text-sm font-semibold rounded-xl hover:bg-muted/50 transition-all disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin text-primary" : ""}`} /> Refresh Activity
        </button>
      </div>

      {/* Filter Bar & Search */}
      <div className="flex flex-col sm:flex-row gap-4 justify-between bg-card border border-border p-4 rounded-2xl shadow-sm">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-2.5 w-4 h-4 text-muted-foreground" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search email, action, or resource..."
            className="w-full bg-background border border-border rounded-xl pl-10 pr-4 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-primary"
          />
        </div>

        <div className="flex items-center gap-3">
          <Filter className="w-4 h-4 text-muted-foreground" />
          <select
            value={filterAction}
            onChange={(e) => setFilterAction(e.target.value)}
            className="bg-background border border-border text-foreground px-3 py-2 rounded-xl text-sm font-semibold focus:outline-none focus:ring-1 focus:ring-primary cursor-pointer"
          >
            <option value="">All Action Types</option>
            <option value="user_login">User Login</option>
            <option value="borrower_created">Entity Registered</option>
            <option value="document_uploaded">Document Uploaded</option>
            <option value="sec_filing_submitted">SEC Filing Ingested</option>
            <option value="risk_pipeline_executed">Risk Pipeline Run</option>
            <option value="credit_memo_generated">Credit Memo Export</option>
          </select>
        </div>
      </div>

      {/* Logs Table */}
      <div className="bg-card border border-border rounded-2xl shadow-sm overflow-hidden">
        {loading ? (
          <div className="py-20 text-center text-muted-foreground flex flex-col items-center">
            <Activity className="w-8 h-8 animate-spin text-primary mb-2" />
            <p className="font-semibold text-sm">Querying Audit Trail...</p>
          </div>
        ) : filteredLogs.length === 0 ? (
          <div className="py-16 text-center text-muted-foreground space-y-2">
            <History className="w-10 h-10 opacity-30 mx-auto" />
            <p className="font-semibold text-base">No audit events recorded yet</p>
            <p className="text-xs">User actions and AI pipeline operations will appear here.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm border-collapse">
              <thead>
                <tr className="border-b border-border bg-muted/40 text-xs uppercase tracking-wider text-muted-foreground font-semibold">
                  <th className="px-6 py-3.5">Timestamp</th>
                  <th className="px-6 py-3.5">Action Event</th>
                  <th className="px-6 py-3.5">User / Initiator</th>
                  <th className="px-6 py-3.5">Target Resource</th>
                  <th className="px-6 py-3.5">Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {filteredLogs.map((log) => {
                  const meta = ACTION_COLORS[log.action] ?? {
                    bg: "bg-muted border-border",
                    text: "text-muted-foreground",
                    label: log.action.replace(/_/g, " "),
                  };

                  return (
                    <tr key={log.id} className="hover:bg-muted/30 transition-colors">
                      <td className="px-6 py-4 whitespace-nowrap text-xs text-muted-foreground font-mono">
                        {new Date(log.created_at).toLocaleString()}
                      </td>

                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold border ${meta.bg} ${meta.text}`}>
                          {meta.label}
                        </span>
                      </td>

                      <td className="px-6 py-4 whitespace-nowrap text-xs font-medium text-foreground">
                        {log.user_email || log.user_id || "System Engine"}
                      </td>

                      <td className="px-6 py-4 whitespace-nowrap text-xs font-mono text-muted-foreground uppercase">
                        {log.resource_type} {log.resource_id ? `#${log.resource_id.slice(0, 8)}` : ""}
                      </td>

                      <td className="px-6 py-4 text-xs font-mono text-muted-foreground max-w-xs truncate">
                        {log.details ? log.details : "—"}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
