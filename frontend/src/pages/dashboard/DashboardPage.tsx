import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import {
  Sparkles, TrendingUp, ShieldCheck, AlertTriangle,
  FileText, Loader2, CheckCircle2, Clock, ChevronRight,
  Database, Users, BarChart3,
} from "lucide-react";
import { useAuthStore } from "@/store/auth.store";
import api from "@/lib/api";

interface RecentDoc {
  agreement_id: string;
  loan_id: string;
  file_path: string;
  document_type: string;
  processing_status: string;
  upload_date: string;
  page_count?: number;
  chunk_count?: number;
}

interface PortfolioStats {
  totalLoans: number;
  totalBorrowers: number;
  totalDocuments: number;
  processedDocuments: number;
  totalCovenants: number;
}

const STATUS_CHIP: Record<string, { label: string; cls: string }> = {
  done:     { label: "Complete",  cls: "text-emerald-400 bg-emerald-400/10 border-emerald-400/20" },
  failed:   { label: "Failed",    cls: "text-destructive bg-destructive/10 border-destructive/20" },
  pending:  { label: "Pending",   cls: "text-muted-foreground bg-muted/50 border-border" },
};

function StatusChip({ status }: { status: string }) {
  const isProcessing = !["done", "failed", "pending"].includes(status);
  if (isProcessing) {
    return (
      <span className="inline-flex items-center gap-1 text-xs font-medium px-2 py-0.5 rounded-full border text-blue-400 bg-blue-400/10 border-blue-400/20">
        <Loader2 className="w-2.5 h-2.5 animate-spin" /> Processing
      </span>
    );
  }
  const meta = STATUS_CHIP[status] ?? STATUS_CHIP["pending"];
  return (
    <span className={`inline-flex items-center gap-1 text-xs font-medium px-2 py-0.5 rounded-full border ${meta.cls}`}>
      {status === "done" ? <CheckCircle2 className="w-2.5 h-2.5" /> : <Clock className="w-2.5 h-2.5" />}
      {meta.label}
    </span>
  );
}

export default function DashboardPage() {
  const { user } = useAuthStore();
  const navigate = useNavigate();

  const [recentDocs, setRecentDocs] = useState<RecentDoc[]>([]);
  const [stats, setStats] = useState<PortfolioStats | null>(null);
  const [loadingStats, setLoadingStats] = useState(true);

  useEffect(() => {
    async function loadDashboard() {
      try {
        const [loansRes, borrowersRes] = await Promise.all([
          api.get("/api/v1/loans/"),
          api.get("/api/v1/borrowers/"),
        ]);

        const loans = loansRes.data ?? [];
        const borrowers = borrowersRes.data ?? [];

        // Load documents for each loan (first 3 loans max to avoid overload)
        const docPromises = loans.slice(0, 5).map((l: any) =>
          api.get(`/api/v1/documents/loan/${l.id}`).then((r) => r.data).catch(() => [])
        );
        const docGroups: RecentDoc[][] = await Promise.all(docPromises);
        const allDocs = docGroups.flat().sort(
          (a, b) => new Date(b.upload_date).getTime() - new Date(a.upload_date).getTime()
        );

        const processed = allDocs.filter((d) => d.processing_status === "done");

        // Count covenants across processed docs
        const covCountPromises = processed.slice(0, 5).map((d) =>
          api.get(`/api/v1/documents/${d.agreement_id}/covenants`)
            .then((r) => r.data.length)
            .catch(() => 0)
        );
        const covCounts: number[] = await Promise.all(covCountPromises);
        const totalCovenants = covCounts.reduce((a, b) => a + b, 0);

        setStats({
          totalLoans: loans.length,
          totalBorrowers: borrowers.length,
          totalDocuments: allDocs.length,
          processedDocuments: processed.length,
          totalCovenants,
        });
        setRecentDocs(allDocs.slice(0, 6));
      } catch (e) {
        console.error("Dashboard load failed", e);
      } finally {
        setLoadingStats(false);
      }
    }
    loadDashboard();
  }, []);

  const kpiCards = [
    {
      title: "Loans Under Management",
      value: loadingStats ? "—" : String(stats?.totalLoans ?? 0),
      sub: "Active loan facilities",
      icon: TrendingUp,
      warning: false,
    },
    {
      title: "Total Borrowers",
      value: loadingStats ? "—" : String(stats?.totalBorrowers ?? 0),
      sub: "Monitored entities",
      icon: Users,
      warning: false,
    },
    {
      title: "Documents Processed",
      value: loadingStats ? "—" : `${stats?.processedDocuments ?? 0} / ${stats?.totalDocuments ?? 0}`,
      sub: "AI pipeline complete",
      icon: Database,
      warning: false,
    },
    {
      title: "Covenants Extracted",
      value: loadingStats ? "—" : String(stats?.totalCovenants ?? 0),
      sub: "Via LLM extraction",
      icon: ShieldCheck,
      warning: (stats?.totalCovenants ?? 0) === 0 && !loadingStats,
    },
  ];

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Portfolio Overview</h1>
        <p className="text-muted-foreground mt-1">
          Welcome back, <strong>{user?.name}</strong>. AI pipeline status and covenant intelligence.
        </p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        {kpiCards.map(({ title, value, sub, icon: Icon, warning }) => (
          <div key={title} className="bg-card border border-border p-5 rounded-xl relative shadow-sm">
            <div className="flex justify-between items-start mb-3">
              <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">{title}</p>
              <div className={`p-2 rounded-lg border ${
                warning
                  ? "bg-amber-400/10 border-amber-400/20 text-amber-400"
                  : "bg-primary/10 border-primary/20 text-primary"
              }`}>
                {loadingStats
                  ? <Loader2 className="w-4 h-4 animate-spin" />
                  : <Icon className="w-4 h-4" />}
              </div>
            </div>
            <p className="text-3xl font-bold">{value}</p>
            <p className="text-xs text-muted-foreground mt-1">{sub}</p>
          </div>
        ))}
      </div>

      {/* AI Insight Banner */}
      <div className="p-6 bg-gradient-to-r from-primary/10 via-violet-500/5 to-blue-500/10 border border-primary/20 rounded-xl flex items-start gap-4">
        <div className="p-2 bg-primary/20 rounded-lg text-primary shrink-0 mt-0.5">
          <Sparkles className="w-5 h-5 animate-pulse" />
        </div>
        <div className="space-y-1">
          <h4 className="font-bold text-primary">Covenexa AI Copilot</h4>
          <p className="text-sm text-muted-foreground leading-relaxed">
            {stats?.totalCovenants && stats.totalCovenants > 0
              ? `${stats.totalCovenants} covenants extracted across ${stats.processedDocuments} processed document(s). Upload financial statements to calculate real-time leverage and coverage ratios.`
              : "Upload a loan agreement to start AI covenant extraction. Cohere Command A will identify maintenance covenants, thresholds, and cure periods automatically."}
          </p>
        </div>
      </div>

      {/* Recent Documents */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-bold flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-primary" />
            Recent Documents
          </h2>
          <button
            onClick={() => navigate("/uploads")}
            className="text-xs text-primary hover:underline flex items-center gap-1"
          >
            View all <ChevronRight className="w-3 h-3" />
          </button>
        </div>

        {loadingStats ? (
          <div className="flex items-center justify-center py-12 text-muted-foreground">
            <Loader2 className="w-5 h-5 animate-spin mr-2" /> Loading documents…
          </div>
        ) : recentDocs.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-14 border border-dashed border-border rounded-xl text-muted-foreground text-center">
            <FileText className="w-10 h-10 mb-3 opacity-30" />
            <p className="font-medium">No documents yet</p>
            <p className="text-sm mb-4">Upload a credit agreement to start automated covenant extraction.</p>
            <button
              onClick={() => navigate("/uploads")}
              className="text-sm text-primary-foreground bg-primary px-4 py-2 rounded-lg hover:bg-primary/90 transition-colors"
            >
              Upload First Document
            </button>
          </div>
        ) : (
          <div className="bg-card border border-border rounded-xl overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border bg-muted/30">
                  <th className="px-5 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wider">Document</th>
                  <th className="px-5 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wider hidden md:table-cell">Type</th>
                  <th className="px-5 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wider hidden sm:table-cell">Uploaded</th>
                  <th className="px-5 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wider">Status</th>
                  <th className="px-3 py-3"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {recentDocs.map((doc) => (
                  <tr
                    key={doc.agreement_id}
                    className="hover:bg-muted/20 cursor-pointer transition-colors"
                    onClick={() => navigate(`/documents/${doc.agreement_id}`)}
                  >
                    <td className="px-5 py-3.5">
                      <div className="flex items-center gap-2.5">
                        <FileText className="w-4 h-4 text-primary shrink-0" />
                        <span className="font-medium truncate max-w-[200px]">
                          {doc.file_path.split("/").pop() ?? doc.agreement_id.slice(0, 16)}
                        </span>
                      </div>
                    </td>
                    <td className="px-5 py-3.5 hidden md:table-cell">
                      <span className="capitalize text-muted-foreground text-xs">{doc.document_type.replace(/_/g, " ")}</span>
                    </td>
                    <td className="px-5 py-3.5 hidden sm:table-cell text-muted-foreground text-xs">
                      {new Date(doc.upload_date).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })}
                    </td>
                    <td className="px-5 py-3.5">
                      <StatusChip status={doc.processing_status} />
                    </td>
                    <td className="px-3 py-3.5">
                      <ChevronRight className="w-4 h-4 text-muted-foreground" />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Missing API Keys Notice */}
      {stats && stats.processedDocuments > 0 && stats.totalCovenants === 0 && (
        <div className="flex items-start gap-3 p-4 bg-amber-400/5 border border-amber-400/15 rounded-xl text-sm">
          <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
          <div>
            <p className="font-semibold text-amber-400">AI Extraction Keys Missing</p>
            <p className="text-muted-foreground text-xs mt-0.5">
              Documents are parsed but no covenants were extracted because <code className="bg-muted px-1 rounded">COHERE_API_KEY</code> is not set.
              Add your Cohere and Pinecone API keys to <code className="bg-muted px-1 rounded">.env</code> to enable real AI extraction.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
