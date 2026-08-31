import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Building2,
  Trash2,
  AlertTriangle,
  X,
  Loader2,
  CheckCircle2,
  Calendar,
  Tag,
  Hash,
  Users,
  FileText,
  Briefcase,
  UserPlus,
  Shield,
  Copy,
  Check,
  Mail,
  User,
} from "lucide-react";
import api from "@/lib/api";
import { useAuthStore } from "@/store/auth.store";
import { useCompanyStore } from "@/store/company.store";
import { Organization } from "@/types";

interface OrgDetail extends Organization {
  stats: {
    borrower_count: number;
    loan_count: number;
    agreement_count: number;
  };
}

interface OrgMember {
  id: string;
  name: string;
  email: string;
  role: string;
  created_at: string;
}

interface OrgInvitation {
  id: string;
  email: string;
  name?: string;
  role: string;
  token: string;
  status: string;
  created_at: string;
  invite_url?: string;
}

export default function OrganizationSettingsPage() {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();

  const [org, setOrg] = useState<OrgDetail | null>(null);
  const [members, setMembers] = useState<OrgMember[]>([]);
  const [invitations, setInvitations] = useState<OrgInvitation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Invite modal state
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteName, setInviteName] = useState("");
  const [inviteRole, setInviteRole] = useState("ANALYST");
  const [inviteSubmitting, setInviteSubmitting] = useState(false);
  const [inviteResult, setInviteResult] = useState<OrgInvitation | null>(null);
  const [inviteError, setInviteError] = useState("");
  const [copied, setCopied] = useState(false);

  // Role edit state
  const [updatingUserId, setUpdatingUserId] = useState<string | null>(null);

  // Delete modal state
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [confirmName, setConfirmName] = useState("");
  const [deleteLoading, setDeleteLoading] = useState(false);
  const [deleteError, setDeleteError] = useState("");

  const isAdmin = user?.role === "ADMIN";

  useEffect(() => {
    loadOrgData();
  }, [user]);

  async function loadOrgData() {
    setLoading(true);
    setError("");
    try {
      // 1. Fetch user's organization
      const orgsRes = await api.get("/api/v1/organizations/");
      const orgList: Organization[] = orgsRes.data || [];
      if (orgList.length === 0) {
        setError("No organization profile found for this account.");
        return;
      }

      const activeOrgId = user?.organization_id || orgList[0].id;
      const detailRes = await api.get(`/api/v1/organizations/${activeOrgId}`);
      setOrg(detailRes.data);

      // 2. Fetch members
      const membersRes = await api.get(`/api/v1/organizations/${activeOrgId}/members`).catch(() => ({ data: [] }));
      setMembers(membersRes.data || []);

      // 3. Fetch pending invitations if Admin
      if (isAdmin) {
        const invitesRes = await api.get(`/api/v1/organizations/${activeOrgId}/invitations`).catch(() => ({ data: [] }));
        setInvitations(invitesRes.data || []);
      }
    } catch (e: any) {
      setError(e?.response?.data?.detail || "Failed to load organization settings.");
    } finally {
      setLoading(false);
    }
  }

  async function handleSendInvite(e: React.FormEvent) {
    e.preventDefault();
    if (!org) return;
    setInviteError("");
    setInviteSubmitting(true);
    try {
      const res = await api.post(`/api/v1/organizations/${org.id}/invitations`, {
        email: inviteEmail.trim().toLowerCase(),
        name: inviteName.trim() || undefined,
        role: inviteRole,
      });

      setInviteResult(res.data);
      setInviteEmail("");
      setInviteName("");
      setInviteRole("ANALYST");

      // Refresh invitations list
      const invitesRes = await api.get(`/api/v1/organizations/${org.id}/invitations`);
      setInvitations(invitesRes.data || []);
    } catch (err: any) {
      setInviteError(err.response?.data?.detail || "Failed to create invitation.");
    } finally {
      setInviteSubmitting(false);
    }
  }

  async function handleRevokeInvite(inviteId: string) {
    if (!org) return;
    try {
      await api.delete(`/api/v1/organizations/${org.id}/invitations/${inviteId}`);
      setInvitations((prev) => prev.filter((i) => i.id !== inviteId));
    } catch (err) {
      console.error("Failed to revoke invitation", err);
    }
  }

  async function handleRoleChange(memberId: string, newRole: string) {
    if (!org || !isAdmin) return;
    setUpdatingUserId(memberId);
    try {
      await api.patch(`/api/v1/organizations/${org.id}/members/${memberId}/role`, {
        role: newRole,
      });
      setMembers((prev) =>
        prev.map((m) => (m.id === memberId ? { ...m, role: newRole } : m))
      );
    } catch (err: any) {
      alert(err.response?.data?.detail || "Failed to update member role.");
    } finally {
      setUpdatingUserId(null);
    }
  }

  async function handleRemoveMember(memberId: string, memberName: string) {
    if (!org || !isAdmin) return;
    if (!confirm(`Are you sure you want to remove ${memberName} from this organization?`)) return;

    try {
      await api.delete(`/api/v1/organizations/${org.id}/members/${memberId}`);
      setMembers((prev) => prev.filter((m) => m.id !== memberId));
    } catch (err: any) {
      alert(err.response?.data?.detail || "Failed to remove member.");
    }
  }

  async function handleDeleteOrg() {
    if (!org || confirmName.trim().toUpperCase() !== "DELETE") return;

    setDeleteLoading(true);
    setDeleteError("");
    try {
      await api.delete(`/api/v1/organizations/${org.id}`);

      // Purge state
      useCompanyStore.getState().clearCompanies();
      logout();

      setShowDeleteModal(false);
      navigate("/login");
    } catch (e: any) {
      setDeleteError(e?.response?.data?.detail || "Failed to delete organization.");
    } finally {
      setDeleteLoading(false);
    }
  }

  function copyInviteLink(url: string) {
    const fullUrl = `${window.location.origin}${url}`;
    navigator.clipboard.writeText(fullUrl);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  if (user && user.role !== "ADMIN") {
    return (
      <div className="max-w-xl mx-auto mt-12 bg-white p-8 rounded-2xl border border-[#EEF1F5] shadow-sm text-center space-y-4">
        <div className="w-12 h-12 rounded-2xl bg-amber-100 text-amber-600 flex items-center justify-center mx-auto">
          <Shield className="w-6 h-6" />
        </div>
        <h2 className="text-xl font-bold text-[#111827]">Access Restricted</h2>
        <p className="text-xs text-[#6B7280]">
          Organization Settings and Team Management are restricted to Administrators. As an <strong>{user.role}</strong>, you have access to credit monitoring and portfolio operations.
        </p>
        <button
          onClick={() => navigate("/app")}
          className="px-5 py-2.5 bg-[#111827] text-white rounded-xl text-xs font-semibold hover:bg-black transition-colors"
        >
          Return to Dashboard
        </button>
      </div>
    );
  }

  if (loading && !org) {
    return (
      <div className="flex items-center justify-center min-h-64">
        <Loader2 className="w-6 h-6 animate-spin text-primary" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-4xl">
        <div className="bg-destructive/10 border border-destructive/20 rounded-2xl p-6 text-destructive text-sm">
          {error}
        </div>
      </div>
    );
  }

  if (!org) return null;

  const formattedDate = new Date(org.created_at).toLocaleDateString("en-US", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });

  return (
    <div className="max-w-4xl space-y-8 pb-12">
      {/* ── Header ─────────────────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold text-foreground tracking-tight">
            Organization Settings
          </h1>
          <p className="text-xs md:text-sm text-muted-foreground mt-1">
            Manage your credit institution details, team members, and enterprise configuration.
          </p>
        </div>

        {isAdmin && (
          <button
            onClick={() => {
              setInviteResult(null);
              setInviteError("");
              setShowInviteModal(true);
            }}
            className="flex items-center gap-2 px-4 py-2.5 bg-primary hover:bg-primary/90 text-primary-foreground font-semibold rounded-xl text-xs shadow-sm transition-all shrink-0"
          >
            <UserPlus className="w-4 h-4" />
            <span>Invite Team Member</span>
          </button>
        )}
      </div>

      {/* ── Organization Info Card ──────────────────────────────── */}
      <div className="bg-card border border-border rounded-2xl p-6 shadow-sm space-y-6">
        <div className="flex items-start justify-between">
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center shrink-0 border border-primary/20">
              <Building2 className="w-6 h-6 text-primary" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-foreground">{org.name}</h2>
              <p className="text-xs font-semibold text-muted-foreground">{org.industry}</p>
            </div>
          </div>

          <span className="inline-flex items-center gap-1.5 text-xs font-semibold text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800/40 px-3 py-1 rounded-full">
            <CheckCircle2 className="w-3.5 h-3.5" />
            Active Institution
          </span>
        </div>

        {/* Info Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 pt-2">
          <InfoRow icon={Hash} label="Organization ID" value={org.id.slice(0, 8) + "…"} mono />
          <InfoRow icon={Calendar} label="Member Since" value={formattedDate} />
          <InfoRow icon={Tag} label="Sector / Industry" value={org.industry} />
          <InfoRow icon={Shield} label="Your Access Level" value={user?.role || "ANALYST"} />
        </div>

        {/* Portfolio Summary */}
        <div className="border-t border-border pt-4">
          <p className="text-[11px] font-bold text-muted-foreground uppercase tracking-wider mb-3">
            Active Portfolio Summary
          </p>
          <div className="grid grid-cols-3 gap-3">
            <StatCard icon={Users} label="Borrower Companies" value={org.stats?.borrower_count ?? 0} />
            <StatCard icon={Briefcase} label="Loan Facilities" value={org.stats?.loan_count ?? 0} />
            <StatCard icon={FileText} label="Credit Agreements" value={org.stats?.agreement_count ?? 0} />
          </div>
        </div>
      </div>

      {/* ── Team & Members Management ────────────────────────────── */}
      <div className="bg-card border border-border rounded-2xl p-6 shadow-sm space-y-5">
        <div className="flex items-center justify-between border-b border-border pb-4">
          <div>
            <h3 className="text-base font-bold text-foreground">Team & Role Permissions</h3>
            <p className="text-xs text-muted-foreground mt-0.5">
              Authorized users with access to {org.name}'s credit portfolio.
            </p>
          </div>
          <span className="text-xs font-semibold text-muted-foreground bg-muted/60 px-2.5 py-1 rounded-lg">
            {members.length} Member{members.length !== 1 ? "s" : ""}
          </span>
        </div>

        {/* Members Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-border text-[11px] font-bold uppercase tracking-wider text-muted-foreground">
                <th className="py-3 px-3">Team Member</th>
                <th className="py-3 px-3">Email Address</th>
                <th className="py-3 px-3">Platform Role</th>
                <th className="py-3 px-3">Joined</th>
                {isAdmin && <th className="py-3 px-3 text-right">Actions</th>}
              </tr>
            </thead>
            <tbody className="divide-y divide-border text-xs">
              {members.map((m) => {
                const isSelf = m.id === user?.id;
                const isMemberAdmin = m.role === "ADMIN";

                return (
                  <tr key={m.id} className="hover:bg-muted/30 transition-colors">
                    <td className="py-3.5 px-3">
                      <div className="flex items-center gap-2.5">
                        <div className="w-7 h-7 rounded-full bg-primary/10 text-primary font-bold text-xs flex items-center justify-center shrink-0">
                          {m.name.charAt(0).toUpperCase()}
                        </div>
                        <div>
                          <p className="font-bold text-foreground">
                            {m.name} {isSelf && <span className="text-[10px] text-primary font-medium">(You)</span>}
                          </p>
                        </div>
                      </div>
                    </td>

                    <td className="py-3.5 px-3 text-muted-foreground font-mono">
                      {m.email}
                    </td>

                    <td className="py-3.5 px-3">
                      {isAdmin && !isSelf ? (
                        <select
                          value={m.role}
                          disabled={updatingUserId === m.id}
                          onChange={(e) => handleRoleChange(m.id, e.target.value)}
                          className="bg-background border border-border rounded-lg px-2 py-1 text-xs font-semibold focus:outline-none focus:ring-1 focus:ring-primary cursor-pointer"
                        >
                          <option value="ADMIN">ADMIN</option>
                          <option value="MANAGER">MANAGER</option>
                          <option value="ANALYST">ANALYST</option>
                        </select>
                      ) : (
                        <span
                          className={`inline-flex items-center px-2 py-0.5 rounded-md font-bold text-[10px] ${
                            isMemberAdmin
                              ? "bg-purple-100 dark:bg-purple-950/50 text-purple-700 dark:text-purple-300"
                              : m.role === "MANAGER"
                              ? "bg-blue-100 dark:bg-blue-950/50 text-blue-700 dark:text-blue-300"
                              : "bg-emerald-100 dark:bg-emerald-950/50 text-emerald-700 dark:text-emerald-300"
                          }`}
                        >
                          {m.role}
                        </span>
                      )}
                    </td>

                    <td className="py-3.5 px-3 text-muted-foreground">
                      {new Date(m.created_at).toLocaleDateString("en-US", {
                        month: "short",
                        day: "numeric",
                        year: "numeric",
                      })}
                    </td>

                    {isAdmin && (
                      <td className="py-3.5 px-3 text-right">
                        {!isSelf && (
                          <button
                            onClick={() => handleRemoveMember(m.id, m.name)}
                            className="p-1 text-muted-foreground hover:text-destructive rounded hover:bg-destructive/10 transition-colors"
                            title="Remove member"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        )}
                      </td>
                    )}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {/* Pending Invitations Table (Admin Only) */}
        {isAdmin && invitations.length > 0 && (
          <div className="pt-4 border-t border-border space-y-3">
            <p className="text-xs font-bold text-muted-foreground uppercase tracking-wider">
              Pending Invitations ({invitations.length})
            </p>
            <div className="space-y-2">
              {invitations.map((inv) => (
                <div
                  key={inv.id}
                  className="flex items-center justify-between p-3 bg-muted/30 border border-border rounded-xl text-xs"
                >
                  <div className="flex items-center gap-3">
                    <Mail className="w-4 h-4 text-primary shrink-0" />
                    <div>
                      <p className="font-bold text-foreground">
                        {inv.email} {inv.name && <span className="text-muted-foreground">({inv.name})</span>}
                      </p>
                      <p className="text-[11px] text-muted-foreground">
                        Role: <strong>{inv.role}</strong> • Status: <span className="text-amber-500 font-semibold">{inv.status}</span>
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => copyInviteLink(inv.invite_url || `/register?invite=${inv.token}`)}
                      className="px-2.5 py-1 bg-background border border-border hover:bg-muted rounded-lg text-xs font-semibold transition-colors flex items-center gap-1"
                    >
                      <Copy className="w-3 h-3" />
                      <span>Copy Link</span>
                    </button>
                    <button
                      onClick={() => handleRevokeInvite(inv.id)}
                      className="p-1 text-muted-foreground hover:text-destructive rounded hover:bg-destructive/10 transition-colors"
                      title="Revoke Invitation"
                    >
                      <X className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* ── Danger Zone (Admin Only) ─────────────────────────────── */}
      {isAdmin && (
        <div className="bg-card border border-destructive/30 rounded-2xl p-6 space-y-4">
          <div>
            <h3 className="text-sm font-bold text-destructive flex items-center gap-2">
              <AlertTriangle className="w-4 h-4" />
              Danger Zone
            </h3>
            <p className="text-xs text-muted-foreground mt-1">
              Irreversible actions that permanently delete this organization and all its data.
            </p>
          </div>

          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 bg-destructive/5 rounded-xl border border-destructive/10">
            <div>
              <p className="text-sm font-semibold text-foreground">Delete this organization</p>
              <p className="text-xs text-muted-foreground mt-0.5">
                Permanently removes {org.name}, all borrowers, loans, agreements, documents, and risk intelligence.
              </p>
            </div>
            <button
              onClick={() => {
                setConfirmName("");
                setDeleteError("");
                setShowDeleteModal(true);
              }}
              className="shrink-0 px-4 py-2 bg-card border border-destructive/30 text-destructive text-xs font-semibold rounded-xl hover:bg-destructive/10 transition-colors flex items-center gap-2"
            >
              <Trash2 className="w-3.5 h-3.5" />
              Delete Organization
            </button>
          </div>
        </div>
      )}

      {/* ── Invite Member Modal ──────────────────────────────────── */}
      {showInviteModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="bg-card border border-border w-full max-w-md rounded-2xl shadow-2xl p-6 space-y-5 animate-in fade-in zoom-in-95">
            <div className="flex items-start justify-between border-b border-border pb-3">
              <div className="flex items-center gap-2.5">
                <div className="p-2 bg-primary/10 text-primary rounded-xl">
                  <UserPlus className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-foreground">Invite Team Member</h3>
                  <p className="text-xs text-muted-foreground">Add an analyst or manager to {org.name}</p>
                </div>
              </div>
              <button
                onClick={() => setShowInviteModal(false)}
                className="p-1 text-muted-foreground hover:text-foreground rounded-lg hover:bg-muted transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {inviteResult ? (
              <div className="space-y-4">
                <div className="p-4 bg-emerald-500/10 border border-emerald-500/20 rounded-xl space-y-2">
                  <div className="flex items-center gap-2 text-emerald-400 font-bold text-xs">
                    <CheckCircle2 className="w-4 h-4" />
                    <span>Invitation Generated Successfully</span>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Share this registration link with <strong>{inviteResult.email}</strong> to onboard them as a{" "}
                    <strong>{inviteResult.role}</strong>.
                  </p>
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                    Invitation URL
                  </label>
                  <div className="flex items-center gap-2">
                    <input
                      type="text"
                      readOnly
                      value={`${window.location.origin}${inviteResult.invite_url || `/register?invite=${inviteResult.token}`}`}
                      className="w-full bg-background border border-border rounded-lg px-3 py-2 text-xs font-mono select-all focus:outline-none"
                    />
                    <button
                      onClick={() => copyInviteLink(inviteResult.invite_url || `/register?invite=${inviteResult.token}`)}
                      className="px-3 py-2 bg-primary text-primary-foreground text-xs font-semibold rounded-lg hover:bg-primary/90 flex items-center gap-1 shrink-0"
                    >
                      {copied ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
                      {copied ? "Copied" : "Copy"}
                    </button>
                  </div>
                </div>

                <button
                  onClick={() => setShowInviteModal(false)}
                  className="w-full py-2.5 bg-muted hover:bg-muted/80 text-foreground font-semibold rounded-xl text-xs transition-colors"
                >
                  Done
                </button>
              </div>
            ) : (
              <form onSubmit={handleSendInvite} className="space-y-4">
                {inviteError && (
                  <div className="p-3 bg-destructive/10 border border-destructive/20 text-destructive text-xs rounded-xl">
                    {inviteError}
                  </div>
                )}

                <div className="space-y-1">
                  <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                    Member Name (Optional)
                  </label>
                  <div className="relative">
                    <User className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground/60" />
                    <input
                      type="text"
                      value={inviteName}
                      onChange={(e) => setInviteName(e.target.value)}
                      placeholder="e.g. Jordan Smith"
                      className="w-full bg-background border border-border rounded-lg pl-9 pr-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-primary"
                    />
                  </div>
                </div>

                <div className="space-y-1">
                  <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                    Work Email Address *
                  </label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground/60" />
                    <input
                      type="email"
                      required
                      value={inviteEmail}
                      onChange={(e) => setInviteEmail(e.target.value)}
                      placeholder="jordan@firm.com"
                      className="w-full bg-background border border-border rounded-lg pl-9 pr-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-primary"
                    />
                  </div>
                </div>

                <div className="space-y-1">
                  <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                    Assign Role *
                  </label>
                  <select
                    value={inviteRole}
                    onChange={(e) => setInviteRole(e.target.value)}
                    className="w-full bg-background border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-primary"
                  >
                    <option value="ANALYST">ANALYST (Review contracts, upload statements, credit analysis)</option>
                    <option value="MANAGER">MANAGER (Review and override credit thresholds)</option>
                    <option value="ADMIN">ADMIN (Full organization administrator)</option>
                  </select>
                </div>

                <div className="flex gap-3 pt-2">
                  <button
                    type="button"
                    onClick={() => setShowInviteModal(false)}
                    className="flex-1 py-2.5 border border-border rounded-xl text-xs font-semibold text-muted-foreground hover:bg-muted transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={inviteSubmitting}
                    className="flex-1 py-2.5 bg-primary text-primary-foreground text-xs font-semibold rounded-xl hover:bg-primary/90 transition-all flex items-center justify-center gap-2 disabled:opacity-50"
                  >
                    {inviteSubmitting ? <Loader2 className="w-4 h-4 animate-spin" /> : <UserPlus className="w-4 h-4" />}
                    Create Invitation
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}

      {/* ── Delete Confirmation Modal ────────────────────────────── */}
      {showDeleteModal && org && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="bg-card border border-border w-full max-w-md rounded-2xl shadow-2xl p-6 space-y-5 animate-in fade-in zoom-in-95">
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-destructive/10 flex items-center justify-center">
                  <Trash2 className="w-5 h-5 text-destructive" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-foreground">Delete Organization</h3>
                  <p className="text-xs text-muted-foreground">This action cannot be undone.</p>
                </div>
              </div>
              <button
                onClick={() => setShowDeleteModal(false)}
                className="p-1 text-muted-foreground hover:text-foreground rounded-lg hover:bg-muted transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="bg-destructive/10 border border-destructive/20 rounded-xl p-4 space-y-2">
              <p className="text-sm font-semibold text-destructive">
                You are about to permanently delete <strong>{org.name}</strong>.
              </p>
              <p className="text-xs text-destructive/80">
                This will permanently remove:
              </p>
              <ul className="text-xs text-destructive/80 space-y-0.5 ml-3 list-disc">
                <li>{org.stats?.borrower_count ?? 0} borrower{org.stats?.borrower_count !== 1 ? "s" : ""}</li>
                <li>{org.stats?.loan_count ?? 0} loan facilit{org.stats?.loan_count !== 1 ? "ies" : "y"}</li>
                <li>{org.stats?.agreement_count ?? 0} agreement{org.stats?.agreement_count !== 1 ? "s" : ""} and all documents</li>
                <li>All financial metrics, covenants, risk assessments, and AI intelligence</li>
              </ul>
            </div>

            <div className="space-y-2">
              <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                Type <span className="text-foreground font-bold">"DELETE"</span> to confirm
              </label>
              <input
                type="text"
                value={confirmName}
                onChange={(e) => setConfirmName(e.target.value)}
                placeholder="DELETE"
                className="w-full bg-background border border-border rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-destructive/50 transition-all"
                autoFocus
              />
            </div>

            {deleteError && (
              <div className="p-3 bg-destructive/10 border border-destructive/20 text-destructive text-xs rounded-xl">
                {deleteError}
              </div>
            )}

            <div className="flex gap-3 pt-2">
              <button
                onClick={() => setShowDeleteModal(false)}
                className="flex-1 px-4 py-2.5 border border-border rounded-xl text-xs font-semibold text-muted-foreground hover:bg-muted transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleDeleteOrg}
                disabled={confirmName.trim().toUpperCase() !== "DELETE" || deleteLoading}
                className="flex-1 px-4 py-2.5 bg-destructive text-destructive-foreground text-xs font-semibold rounded-xl hover:bg-destructive/90 transition-colors disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {deleteLoading ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Trash2 className="w-4 h-4" />
                )}
                Delete Organization
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function InfoRow({
  icon: Icon,
  label,
  value,
  mono = false,
}: {
  icon: React.ElementType;
  label: string;
  value: string;
  mono?: boolean;
}) {
  return (
    <div className="flex items-center gap-3">
      <Icon className="w-4 h-4 text-muted-foreground shrink-0" />
      <div className="min-w-0">
        <p className="text-[10px] text-muted-foreground uppercase tracking-wide font-medium">{label}</p>
        <p className={`text-xs font-bold text-foreground truncate ${mono ? "font-mono" : ""}`}>
          {value}
        </p>
      </div>
    </div>
  );
}

function StatCard({
  icon: Icon,
  label,
  value,
}: {
  icon: React.ElementType;
  label: string;
  value: number;
}) {
  return (
    <div className="bg-muted/40 rounded-xl p-3 text-center border border-border">
      <Icon className="w-4 h-4 text-primary mx-auto mb-1" />
      <p className="text-base font-bold text-foreground">{value}</p>
      <p className="text-[10px] text-muted-foreground font-medium">{label}</p>
    </div>
  );
}
