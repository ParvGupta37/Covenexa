import React, { useState } from "react";
import { Link, useNavigate, Navigate } from "react-router-dom";
import { Sparkles, Key, Mail, AlertCircle, Loader2 } from "lucide-react";
import api from "@/lib/api";
import { useAuthStore } from "@/store/auth.store";

export function LoginPage() {
  const navigate = useNavigate();
  const loginStore = useAuthStore((state) => state.login);
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const isLoading = useAuthStore((state) => state.isLoading);

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  if (!isLoading && isAuthenticated) {
    return <Navigate to="/app" replace />;
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      // 1. Authenticate credentials
      const loginRes = await api.post("/api/v1/auth/login", {
        email: email.trim().toLowerCase(),
        password,
      });

      const { access_token, refresh_token, user } = loginRes.data;

      // 2. Cache tokens and user in store
      loginStore(user, access_token, refresh_token);

      // 3. Move cleanly to Dashboard using replace to preserve clean back navigation
      navigate("/app", { replace: true });
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      setError(
        typeof detail === "string"
          ? detail
          : Array.isArray(detail)
          ? detail.map((d: any) => d.msg).join(", ")
          : "Authentication failed. Please verify your email and password."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-indigo-950 via-background to-background py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8 bg-card border border-border p-8 rounded-2xl shadow-xl backdrop-blur-sm">
        {/* Header Title */}
        <div className="flex flex-col items-center">
          <div className="p-3 bg-primary/10 rounded-full border border-primary/20 mb-3">
            <Sparkles className="h-8 w-8 text-primary" />
          </div>
          <h2 className="text-3xl font-extrabold tracking-tight">Sign in to Covenexa</h2>
          <p className="mt-1 text-sm text-muted-foreground">AI Operating System for Private Credit</p>
        </div>

        {/* Input Form */}
        <form className="mt-8 space-y-4" onSubmit={handleSubmit}>
          {error && (
            <div className="p-3.5 bg-destructive/10 border border-destructive/20 text-destructive text-xs rounded-xl flex items-center gap-2">
              <AlertCircle className="h-4 w-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <div className="space-y-4">
            <div className="space-y-1">
              <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Email Address</label>
              <div className="relative">
                <Mail className="absolute left-3 top-3 h-4 w-4 text-muted-foreground/60" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@covenexa.in"
                  className="w-full bg-background border border-border rounded-lg pl-10 pr-4 py-2.5 text-sm focus:outline-none focus:ring-1 focus:ring-primary focus:border-primary transition-all placeholder:text-muted-foreground/40"
                />
              </div>
            </div>

            <div className="space-y-1">
              <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Password</label>
              <div className="relative">
                <Key className="absolute left-3 top-3 h-4 w-4 text-muted-foreground/60" />
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full bg-background border border-border rounded-lg pl-10 pr-4 py-2.5 text-sm focus:outline-none focus:ring-1 focus:ring-primary focus:border-primary transition-all placeholder:text-muted-foreground/40"
                />
              </div>
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full mt-4 flex items-center justify-center py-2.5 px-4 border border-transparent rounded-lg text-sm font-semibold text-primary-foreground bg-primary hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary disabled:opacity-50 disabled:cursor-not-allowed transition-all gap-2"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Authenticating...</span>
              </>
            ) : (
              "Sign In"
            )}
          </button>
        </form>

        {/* Footer Redirect link */}
        <div className="text-center pt-2">
          <p className="text-xs text-muted-foreground">
            Don't have an organization account?{" "}
            <Link to="/register" className="font-semibold text-primary hover:text-primary/80 transition-colors">
              Create Lender Account
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
