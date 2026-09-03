import React, { useState, useEffect } from "react";
import { Link, useNavigate, useSearchParams, Navigate } from "react-router-dom";
import {
  Sparkles,
  Key,
  Mail,
  User,
  Building2,
  Briefcase,
  AlertCircle,
  CheckCircle2,
  XCircle,
  Loader2,
  Users,
} from "lucide-react";
import api from "@/lib/api";
import { useAuthStore } from "@/store/auth.store";

interface PasswordRule {
  label: string;
  test: (pw: string) => boolean;
}

const PASSWORD_RULES: PasswordRule[] = [
  { label: "At least 8 characters", test: (pw) => pw.length >= 8 },
  { label: "One uppercase letter (A–Z)", test: (pw) => /[A-Z]/.test(pw) },
  { label: "One lowercase letter (a–z)", test: (pw) => /[a-z]/.test(pw) },
  { label: "One digit (0–9)", test: (pw) => /\d/.test(pw) },
  { label: "One special character (!@#$%…)", test: (pw) => /[ !@#$%^&*()_+=\-\[\]{}|;:'",.<>?/`~]/.test(pw) },
];

export function RegisterPage() {
  const navigate = useNavigate();
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const isLoading = useAuthStore((state) => state.isLoading);

  const [searchParams] = useSearchParams();
  const inviteTokenFromUrl = searchParams.get("invite") || "";

  // Mode: "org" (New organization signup) or "invite" (Join via invitation)
  const [mode, setMode] = useState<"org" | "invite">(inviteTokenFromUrl ? "invite" : "org");

  // Common fields
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showRules, setShowRules] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  if (!isLoading && isAuthenticated && !inviteTokenFromUrl) {
    return <Navigate to="/app" replace />;
  }

  // Org signup specific
  const [orgName, setOrgName] = useState("");
  const [orgIndustry, setOrgIndustry] = useState("Private Credit");

  // Invite specific
  const [inviteToken, setInviteToken] = useState(inviteTokenFromUrl);
  const [inviteData, setInviteData] = useState<{
    email: string;
    name?: string;
    role: string;
    organization_name: string;
  } | null>(null);
  const [inviteVerifying, setInviteVerifying] = useState(false);

  const passwordValid = PASSWORD_RULES.every((r) => r.test(password));

  // Verify invitation token if present
  useEffect(() => {
    if (inviteToken.trim()) {
      setInviteVerifying(true);
      api
        .get(`/api/v1/auth/verify-invite/${inviteToken.trim()}`)
        .then((res) => {
          setInviteData(res.data);
          setEmail(res.data.email);
          if (res.data.name) setName(res.data.name);
          setMode("invite");
        })
        .catch((err) => {
          setInviteData(null);
          setError(err.response?.data?.detail || "Invalid or expired invitation link.");
        })
        .finally(() => setInviteVerifying(false));
    }
  }, [inviteToken]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (!passwordValid) {
      setError("Password does not meet strength requirements. Please review the rules below.");
      setShowRules(true);
      return;
    }

    setLoading(true);
    try {
      if (mode === "invite") {
        // Accept invitation
        const res = await api.post("/api/v1/auth/accept-invite", {
          token: inviteToken.trim(),
          name: name.trim(),
          password,
        });

        // Store auth tokens and user via central login action
        useAuthStore.getState().login(
          res.data.user,
          res.data.access_token,
          res.data.refresh_token
        );

        navigate("/app", { replace: true });
      } else {
        // New Organization Signup
        if (!orgName.trim()) {
          setError("Please provide an organization name.");
          setLoading(false);
          return;
        }

        const res = await api.post("/api/v1/auth/signup-org", {
          name: name.trim(),
          email: email.trim().toLowerCase(),
          password,
          organization_name: orgName.trim(),
          organization_industry: orgIndustry,
        });

        // Log user straight in via central login action
        useAuthStore.getState().login(
          res.data.user,
          res.data.access_token,
          res.data.refresh_token
        );

        navigate("/app", { replace: true });
      }
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      setError(
        typeof detail === "string"
          ? detail
          : Array.isArray(detail)
          ? detail.map((d: any) => d.msg).join(", ")
          : "Registration failed. Please try again."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-indigo-950 via-background to-background py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-lg w-full space-y-6 bg-card border border-border p-8 rounded-2xl shadow-xl backdrop-blur-sm">
        {/* Header */}
        <div className="flex flex-col items-center text-center">
          <div className="p-3 bg-primary/10 rounded-full border border-primary/20 mb-3">
            <Sparkles className="h-7 w-7 text-primary" />
          </div>
          <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-foreground">
            {mode === "invite" ? "Join Organization" : "Create Lender Account"}
          </h2>
          <p className="mt-1 text-xs sm:text-sm text-muted-foreground">
            {mode === "invite"
              ? "Complete your profile to join your team"
              : "Register your private credit fund on Covenexa"}
          </p>
        </div>

        {/* Mode Switch Tabs */}
        {!inviteTokenFromUrl && (
          <div className="grid grid-cols-2 p-1 bg-muted/60 rounded-xl text-xs font-semibold">
            <button
              type="button"
              onClick={() => { setMode("org"); setError(""); }}
              className={`py-2 rounded-lg transition-all flex items-center justify-center gap-1.5 ${
                mode === "org"
                  ? "bg-card text-foreground shadow-sm"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <Building2 className="w-3.5 h-3.5" />
              <span>New Organization</span>
            </button>
            <button
              type="button"
              onClick={() => { setMode("invite"); setError(""); }}
              className={`py-2 rounded-lg transition-all flex items-center justify-center gap-1.5 ${
                mode === "invite"
                  ? "bg-card text-foreground shadow-sm"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <Users className="w-3.5 h-3.5" />
              <span>Join with Invite</span>
            </button>
          </div>
        )}

        {/* Invite Verification Banner */}
        {mode === "invite" && (
          <div className="space-y-3">
            {inviteVerifying ? (
              <div className="p-3 bg-muted/40 rounded-xl text-xs text-muted-foreground flex items-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin text-primary" />
                <span>Verifying invitation token...</span>
              </div>
            ) : inviteData ? (
              <div className="p-4 bg-emerald-500/10 border border-emerald-500/20 rounded-xl space-y-1">
                <p className="text-xs font-semibold text-emerald-400">
                  ✓ Valid Invitation
                </p>
                <p className="text-sm font-bold text-foreground">
                  {inviteData.organization_name}
                </p>
                <p className="text-xs text-muted-foreground">
                  Role: <strong className="text-foreground">{inviteData.role}</strong> • Email: {inviteData.email}
                </p>
              </div>
            ) : (
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  Invitation Token *
                </label>
                <input
                  type="text"
                  value={inviteToken}
                  onChange={(e) => setInviteToken(e.target.value)}
                  placeholder="Paste your 32-character invite token"
                  required
                  className="w-full bg-background border border-border rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-primary font-mono"
                />
              </div>
            )}
          </div>
        )}

        {/* Error Alert */}
        {error && (
          <div className="p-3 bg-destructive/10 border border-destructive/20 text-destructive text-xs rounded-lg flex items-center gap-2">
            <AlertCircle className="h-4 w-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Form */}
        <form className="space-y-4" onSubmit={handleSubmit}>
          {/* Organization Fields (Only in Org Mode) */}
          {mode === "org" && (
            <div className="p-4 bg-muted/30 border border-border rounded-xl space-y-3">
              <div className="flex items-center gap-2 text-xs font-bold text-foreground uppercase tracking-wider">
                <Building2 className="w-4 h-4 text-primary" />
                <span>Lender Organization Details</span>
              </div>

              <div className="space-y-1">
                <label className="text-xs font-semibold text-muted-foreground">Organization Name *</label>
                <input
                  type="text"
                  required
                  value={orgName}
                  onChange={(e) => setOrgName(e.target.value)}
                  placeholder="e.g. Blue Owl Demo Credit, Ares Management"
                  className="w-full bg-background border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-primary"
                />
              </div>

              <div className="space-y-1">
                <label className="text-xs font-semibold text-muted-foreground">Industry Sector</label>
                <div className="relative">
                  <Briefcase className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground/60" />
                  <select
                    value={orgIndustry}
                    onChange={(e) => setOrgIndustry(e.target.value)}
                    className="w-full bg-background border border-border rounded-lg pl-9 pr-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-primary"
                  >
                    <option value="Private Credit">Private Credit</option>
                    <option value="Direct Lending">Direct Lending</option>
                    <option value="Asset Management">Asset Management</option>
                    <option value="Investment Banking">Investment Banking</option>
                    <option value="Commercial Banking">Commercial Banking</option>
                    <option value="Hedge Fund">Hedge Fund</option>
                    <option value="Other">Other Financial Services</option>
                  </select>
                </div>
              </div>
            </div>
          )}

          {/* User Fields */}
          <div className="space-y-3">
            {/* Full Name */}
            <div className="space-y-1">
              <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                Full Name *
              </label>
              <div className="relative">
                <User className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground/60" />
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Alex Morgan"
                  className="w-full bg-background border border-border rounded-lg pl-9 pr-4 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-primary"
                />
              </div>
            </div>

            {/* Email */}
            <div className="space-y-1">
              <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                Work Email Address *
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground/60" />
                <input
                  type="email"
                  required
                  disabled={mode === "invite" && !!inviteData?.email}
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="alex@blueowldemo.com"
                  className="w-full bg-background border border-border rounded-lg pl-9 pr-4 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-primary disabled:opacity-60"
                />
              </div>
            </div>

            {/* Password */}
            <div className="space-y-1">
              <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                Password *
                {password.length > 0 && (
                  <span className={`ml-2 font-normal normal-case ${passwordValid ? "text-green-500" : "text-amber-500"}`}>
                    {passwordValid ? "✓ Strong" : "Weak"}
                  </span>
                )}
              </label>
              <div className="relative">
                <Key className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground/60" />
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => { setPassword(e.target.value); setShowRules(true); }}
                  onFocus={() => setShowRules(true)}
                  placeholder="••••••••"
                  className="w-full bg-background border border-border rounded-lg pl-9 pr-4 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-primary"
                />
              </div>

              {/* Password strength rules */}
              {showRules && (
                <ul className="mt-2 space-y-1 p-2.5 bg-muted/40 rounded-lg border border-border">
                  {PASSWORD_RULES.map((rule) => {
                    const passes = rule.test(password);
                    return (
                      <li key={rule.label} className="flex items-center gap-2 text-xs">
                        {passes ? (
                          <CheckCircle2 className="h-3 w-3 text-green-500 shrink-0" />
                        ) : (
                          <XCircle className="h-3 w-3 text-muted-foreground/50 shrink-0" />
                        )}
                        <span className={passes ? "text-green-600 dark:text-green-400" : "text-muted-foreground"}>
                          {rule.label}
                        </span>
                      </li>
                    );
                  })}
                </ul>
              )}
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full mt-4 flex justify-center py-2.5 px-4 border border-transparent rounded-lg text-sm font-semibold text-primary-foreground bg-primary hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-primary disabled:opacity-50 disabled:cursor-not-allowed transition-all"
          >
            {loading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : mode === "invite" ? (
              "Accept Invitation & Join"
            ) : (
              "Create Organization & Start Free"
            )}
          </button>
        </form>

        {/* Footer */}
        <div className="text-center pt-2">
          <p className="text-xs text-muted-foreground">
            Already have an account?{" "}
            <Link to="/login" className="font-semibold text-primary hover:text-primary/80 transition-colors">
              Sign In Instead
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
