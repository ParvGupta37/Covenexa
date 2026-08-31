import { useState, useEffect } from "react";
import { History, Activity, Filter, RefreshCw, Search } from "lucide-react";
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
    <div className="space-y-8 pb-12">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold text-[#111827] tracking-tight">
            Audit Trail & Activity Logs
          </h1>
          <p className="text-xs md:text-sm font-medium text-[#6B7280] mt-1">
            Complete immutable audit trail of user actions, AI pipeline executions, and risk intelligence events.
          </p>
        </div>

        <button
          onClick={fetchLogs}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2.5 bg-white border border-[#EEF1F5] hover:bg-gray-50 text-[#111827] font-semibold rounded-xl text-xs shadow-sm transition-all disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
          <span>Refresh Audit Trail</span>
        </button>
      </div>

      <div className="bg-white rounded-2xl p-4 border border-[#EEF1F5] shadow-[0_4px_20px_rgba(17,24,39,0.03)] flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="relative w-full sm:w-80">
          <Search className="absolute left-3.5 top-2.5 w-4 h-4 text-[#9CA3AF]" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search email, action, or resource..."
            className="w-full bg-[#F8F9FC] border border-[#EEF1F5] rounded-xl pl-10 pr-4 py-2 text-xs font-medium text-[#111827] focus:outline-none focus:ring-2 focus:ring-[#7C8DFB]/50"
          />
        </div>

        <div className="flex items-center gap-2">
          <Filter className="w-3.5 h-3.5 text-[#9CA3AF]" />
          <select
            value={filterAction}
            onChange={(e) => setFilterAction(e.target.value)}
            className="bg-[#F8F9FC] border border-[#EEF1F5] text-[#111827] px-3 py-2 rounded-xl text-xs font-semibold focus:outline-none"
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

      <div className="bg-white rounded-2xl border border-[#EEF1F5] shadow-[0_4px_20px_rgba(17,24,39,0.03)] overflow-hidden">
        {loading ? (
          <div className="py-20 text-center text-[#6B7280]">
            <Activity className="w-6 h-6 animate-spin text-[#7C8DFB] mx-auto mb-2" />
            <p className="text-xs font-semibold">Querying Audit Trail...</p>
          </div>
        ) : filteredLogs.length === 0 ? (
          <div className="py-16 text-center text-[#9CA3AF]">
            <History className="w-8 h-8 opacity-40 mx-auto mb-2" />
            <p className="text-xs font-bold text-[#111827]">No audit events recorded</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-[#F8F9FC] border-b border-[#EEF1F5] text-[11px] font-bold uppercase tracking-wider text-[#6B7280]">
                  <th className="py-3.5 px-6">Timestamp</th>
                  <th className="py-3.5 px-4">Action Event</th>
                  <th className="py-3.5 px-4">User / Initiator</th>
                  <th className="py-3.5 px-4">Target Resource</th>
                  <th className="py-3.5 px-6">Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#EEF1F5] text-xs">
                {filteredLogs.map((log) => (
                  <tr key={log.id} className="hover:bg-[#F8F9FC] transition-colors">
                    <td className="py-4 px-6 font-mono text-[#6B7280]">
                      {new Date(log.created_at).toLocaleString()}
                    </td>
                    <td className="py-4 px-4 font-bold text-[#111827]">
                      {log.action.replace(/_/g, " ").toUpperCase()}
                    </td>
                    <td className="py-4 px-4 font-semibold text-[#111827]">
                      {log.user_email || log.user_id || "System Engine"}
                    </td>
                    <td className="py-4 px-4 font-mono text-[#6B7280]">
                      {log.resource_type} {log.resource_id ? `#${log.resource_id.slice(0, 8)}` : ""}
                    </td>
                    <td className="py-4 px-6 font-mono text-[#6B7280] truncate max-w-xs">
                      {log.details || "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
