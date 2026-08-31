import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import {
  Brain,
  ShieldCheck,
  FileSearch,
  Network,
  TrendingUp,
  BarChart3,
  Activity,
  Lock,
  ClipboardList,
  Layers,
  ArrowRight,
  CheckCircle2,
  Menu,
  X,
  ChevronRight,
  Building2,
  DollarSign,
  FileText,
  Scale,
  BrainCircuit,
} from "lucide-react";
import { useAuthStore } from "@/store/auth.store";

// ─── Animated hero visual nodes ────────────────────────────────────────────
const heroNodes = [
  { id: "borrower", label: "Borrower", sub: "Apple Inc.", x: 48, y: 12, color: "#7C8DFB", icon: Building2 },
  { id: "loan", label: "Credit Facility", sub: "$50M Term Loan", x: 26, y: 40, color: "#6366F1", icon: DollarSign },
  { id: "agreement", label: "Agreement", sub: "Credit Facility v1.0", x: 70, y: 40, color: "#8B5CF6", icon: FileText },
  { id: "risk", label: "Health Score", sub: "97.1 / 100 — Prime", x: 14, y: 68, color: "#10B981", icon: Activity },
  { id: "covenant", label: "Covenants", sub: "2 Active Rules", x: 48, y: 68, color: "#F97316", icon: Scale },
  { id: "ai", label: "AI Copilot", sub: "Continuous Monitoring", x: 82, y: 68, color: "#7C8DFB", icon: BrainCircuit },
];

const heroEdges = [
  ["borrower", "loan"],
  ["borrower", "agreement"],
  ["loan", "risk"],
  ["agreement", "covenant"],
  ["covenant", "ai"],
  ["risk", "ai"],
];

// ─── Capability cards ───────────────────────────────────────────────────────
const capabilities = [
  {
    icon: BrainCircuit,
    title: "AI Credit Copilot",
    desc: "Ask questions about borrowers, covenants, and financial data with source-grounded evidence.",
    color: "#7C8DFB",
    bg: "#E8ECFF",
  },
  {
    icon: Activity,
    title: "Risk Monitoring",
    desc: "Continuously evaluate borrower health, liquidity, and leverage signals across your portfolio.",
    color: "#6366F1",
    bg: "#EEF2FF",
  },
  {
    icon: ClipboardList,
    title: "Covenant Monitoring",
    desc: "Track contractual financial requirements and detect threshold breaches with automated headroom checks.",
    color: "#10B981",
    bg: "#D1FAE5",
  },
  {
    icon: FileSearch,
    title: "Document Intelligence",
    desc: "Upload credit agreements and SEC filings to extract covenants and structured metrics instantly.",
    color: "#8B5CF6",
    bg: "#EDE9FE",
  },
  {
    icon: TrendingUp,
    title: "Stress Testing",
    desc: "Simulate multi-variable adverse macroeconomic scenarios and forecast covenant resiliency under pressure.",
    color: "#F97316",
    bg: "#FFEDD5",
  },
  {
    icon: Network,
    title: "Knowledge Graph",
    desc: "Explore connected relational graph networks between borrowers, facilities, agreements, and covenants.",
    color: "#0EA5E9",
    bg: "#E0F2FE",
  },
];

// ─── Data connection cards ──────────────────────────────────────────────────
const dataConnections = [
  { label: "Borrower Data", icon: Building2, color: "#6366F1", bg: "#EEF2FF" },
  { label: "Financial Metrics", icon: BarChart3, color: "#10B981", bg: "#D1FAE5" },
  { label: "Credit Agreements", icon: FileText, color: "#8B5CF6", bg: "#EDE9FE" },
  { label: "Covenants", icon: Scale, color: "#F97316", bg: "#FFEDD5" },
  { label: "Risk Models", icon: Activity, color: "#EF4444", bg: "#FEE2E2" },
  { label: "AI Analysis", icon: BrainCircuit, color: "#7C8DFB", bg: "#E8ECFF" },
];

// ─── How it works steps ─────────────────────────────────────────────────────
const steps = [
  {
    num: "01",
    title: "Connect Your Data",
    desc: "Upload credit agreements, SEC filings, and financial documents into Covenexa.",
    icon: FileSearch,
  },
  {
    num: "02",
    title: "Analyze Risk",
    desc: "Covenexa extracts financial metrics, covenant terms, and evaluates borrower health.",
    icon: BarChart3,
  },
  {
    num: "03",
    title: "Act With Confidence",
    desc: "Receive AI-powered insights, covenant alerts, and recommendations to drive decisions.",
    icon: Brain,
  },
];

// ─── Security points ────────────────────────────────────────────────────────
const securityPoints = [
  { icon: Lock, title: "Authentication", desc: "JWT-based, token-secured access for every session." },
  { icon: ShieldCheck, title: "Role-Based Access Control", desc: "Admin, Manager, and Analyst roles with enforced permissions." },
  { icon: Layers, title: "Tenant Isolation", desc: "Every organization's data is scoped and access-controlled." },
  { icon: ClipboardList, title: "Complete Audit Trail", desc: "Every action is logged with timestamps and user identity." },
  { icon: CheckCircle2, title: "Data Integrity", desc: "Evidence-backed AI responses tied to source documents." },
  { icon: FileSearch, title: "Secure Document Handling", desc: "Documents processed in isolated pipelines, never exposed externally." },
];

// ─── Value strip items ──────────────────────────────────────────────────────
const valueItems = [
  "AI-Powered Analysis",
  "Hybrid GraphRAG",
  "Covenant Monitoring",
  "Portfolio Risk Intelligence",
  "Document Intelligence",
  "Stress Simulation",
];

// ─── Minimal SVG logo ───────────────────────────────────────────────────────
function CovLogo({ size = 28 }: { size?: number }) {
  return (
    <div
      style={{ width: size, height: size }}
      className="rounded-xl bg-[#111827] flex items-center justify-center shrink-0"
    >
      <svg
        width={size * 0.56}
        height={size * 0.56}
        viewBox="0 0 24 24"
        fill="white"
      >
        <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
      </svg>
    </div>
  );
}

// ─── Animated hero graph ────────────────────────────────────────────────────
function HeroGraph() {
  const [visible, setVisible] = useState<string[]>([]);

  useEffect(() => {
    const ids = heroNodes.map((n) => n.id);
    let i = 0;
    const t = setInterval(() => {
      if (i < ids.length) {
        setVisible((prev) => [...prev, ids[i]]);
        i++;
      } else {
        clearInterval(t);
      }
    }, 220);
    return () => clearInterval(t);
  }, []);

  const getPos = (id: string) => {
    const node = heroNodes.find((n) => n.id === id)!;
    return { x: node.x, y: node.y };
  };

  return (
    <div className="relative w-full h-full select-none">
      {/* SVG connection lines */}
      <svg
        className="absolute inset-0 w-full h-full"
        viewBox="0 0 100 85"
        preserveAspectRatio="none"
      >
        {heroEdges.map(([from, to], i) => {
          const f = getPos(from);
          const t = getPos(to);
          const bothVisible = visible.includes(from) && visible.includes(to);
          return (
            <line
              key={i}
              x1={f.x}
              y1={f.y}
              x2={t.x}
              y2={t.y}
              stroke="#E8ECFF"
              strokeWidth="0.8"
              strokeDasharray="3 2"
              style={{
                opacity: bothVisible ? 1 : 0,
                transition: "opacity 0.6s ease",
              }}
            />
          );
        })}
      </svg>

      {/* Nodes */}
      {heroNodes.map((node) => {
        const isVis = visible.includes(node.id);
        const Icon = node.icon;
        return (
          <div
            key={node.id}
            style={{
              position: "absolute",
              left: `${node.x}%`,
              top: `${node.y}%`,
              opacity: isVis ? 1 : 0,
              transform: `translate(-50%, -50%) scale(${isVis ? 1 : 0.6})`,
              transition: "opacity 0.4s ease, transform 0.4s ease",
            }}
          >
            <div className="flex flex-col items-center gap-1">
              <div
                style={{
                  background: node.color + "18",
                  border: `1.5px solid ${node.color}40`,
                  boxShadow: `0 2px 12px ${node.color}20`,
                }}
                className="w-10 h-10 rounded-2xl flex items-center justify-center"
              >
                <Icon className="w-4 h-4" style={{ color: node.color }} />
              </div>
              <div className="text-center">
                <p className="text-[9px] font-bold text-[#111827] leading-none">{node.label}</p>
                <p className="text-[8px] text-[#9CA3AF] leading-tight mt-0.5">{node.sub}</p>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

// ─── Scroll reveal hook ─────────────────────────────────────────────────────
function useReveal() {
  const ref = useRef<HTMLDivElement>(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => { if (entry.isIntersecting) setVisible(true); },
      { threshold: 0.15 }
    );
    if (ref.current) observer.observe(ref.current);
    return () => observer.disconnect();
  }, []);

  return { ref, visible };
}

// ─── Section wrapper with reveal ───────────────────────────────────────────
function RevealSection({
  children,
  className = "",
  delay = 0,
}: {
  children: React.ReactNode;
  className?: string;
  delay?: number;
}) {
  const { ref, visible } = useReveal();
  return (
    <div
      ref={ref}
      className={className}
      style={{
        opacity: visible ? 1 : 0,
        transform: visible ? "translateY(0)" : "translateY(24px)",
        transition: `opacity 0.6s ease ${delay}ms, transform 0.6s ease ${delay}ms`,
      }}
    >
      {children}
    </div>
  );
}

// ─── MAIN COMPONENT ─────────────────────────────────────────────────────────
export function LandingPage() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 30);
    window.addEventListener("scroll", onScroll);
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  const navLinks = [
    { label: "Platform", href: "#capabilities" },
    { label: "How It Works", href: "#how-it-works" },
    { label: "Intelligence", href: "#intelligence" },
    { label: "Security", href: "#security" },
  ];

  return (
    <div className="min-h-screen bg-[#F8F9FC] font-sans text-[#111827] overflow-x-hidden">
      {/* ── NAVBAR ─────────────────────────────────────────────────────────── */}
      <header
        className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
          scrolled
            ? "bg-white/90 backdrop-blur-md border-b border-[#EEF1F5] shadow-sm"
            : "bg-transparent"
        }`}
      >
        <div className="max-w-7xl mx-auto px-6 lg:px-8 h-16 flex items-center justify-between">
          {/* Brand */}
          <Link to="/" className="flex items-center gap-2.5">
            <CovLogo size={32} />
            <span className="text-lg font-bold text-[#111827] tracking-tight">Covenexa</span>
          </Link>

          {/* Desktop Nav */}
          <nav className="hidden md:flex items-center gap-6">
            {navLinks.map((link) => (
              <a
                key={link.label}
                href={link.href}
                className="text-sm font-medium text-[#6B7280] hover:text-[#111827] transition-colors"
              >
                {link.label}
              </a>
            ))}
          </nav>

          {/* Desktop CTAs */}
          <div className="hidden md:flex items-center gap-3">
            {isAuthenticated ? (
              <Link
                to="/app"
                className="inline-flex items-center gap-2 text-sm font-semibold text-white bg-[#111827] hover:bg-[#1F2937] px-4 py-2.5 rounded-xl transition-all shadow-sm shadow-[#111827]/20"
              >
                Launch Platform
                <ArrowRight className="w-4 h-4" />
              </Link>
            ) : (
              <>
                <Link
                  to="/login"
                  className="text-sm font-semibold text-[#6B7280] hover:text-[#111827] transition-colors px-4 py-2"
                >
                  Login
                </Link>
                <Link
                  to="/login"
                  className="text-sm font-semibold text-white bg-[#111827] hover:bg-[#1F2937] px-4 py-2.5 rounded-xl transition-all shadow-sm shadow-[#111827]/20"
                >
                  Get Started
                </Link>
              </>
            )}
          </div>

          {/* Mobile menu toggle */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden p-2 text-[#6B7280]"
          >
            {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>

        {/* Mobile Menu */}
        {mobileMenuOpen && (
          <div className="md:hidden bg-white border-t border-[#EEF1F5] px-6 py-4 space-y-3">
            {navLinks.map((link) => (
              <a
                key={link.label}
                href={link.href}
                onClick={() => setMobileMenuOpen(false)}
                className="block text-sm font-medium text-[#6B7280] hover:text-[#111827] py-1"
              >
                {link.label}
              </a>
            ))}
            <div className="pt-3 border-t border-[#EEF1F5] flex flex-col gap-2">
              {isAuthenticated ? (
                <Link
                  to="/app"
                  className="block text-center py-2.5 text-sm font-semibold text-white bg-[#111827] rounded-xl"
                >
                  Launch Platform
                </Link>
              ) : (
                <>
                  <Link to="/login" className="block text-center py-2.5 text-sm font-semibold text-[#6B7280]">
                    Login
                  </Link>
                  <Link
                    to="/login"
                    className="block text-center py-2.5 text-sm font-semibold text-white bg-[#111827] rounded-xl"
                  >
                    Get Started
                  </Link>
                </>
              )}
            </div>
          </div>
        )}
      </header>

      {/* ── HERO SECTION ───────────────────────────────────────────────────── */}
      <section className="pt-28 pb-20 lg:pt-36 lg:pb-28 px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="grid lg:grid-cols-2 gap-12 lg:gap-16 items-center">
            {/* Hero Copy */}
            <div className="space-y-8">
              {/* Eyebrow */}
              <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-[#E8ECFF] rounded-full">
                <div className="w-1.5 h-1.5 rounded-full bg-[#7C8DFB] animate-pulse" />
                <span className="text-xs font-bold text-[#4F46E5] uppercase tracking-widest">
                  AI-Powered Credit Intelligence
                </span>
              </div>

              {/* Headline */}
              <h1 className="text-4xl sm:text-5xl lg:text-[3.5rem] font-black text-[#111827] leading-[1.08] tracking-tight">
                Turn Credit Risk Into{" "}
                <span className="text-[#7C8DFB]">Actionable</span>{" "}
                Intelligence.
              </h1>

              {/* Supporting text */}
              <p className="text-lg text-[#6B7280] leading-relaxed max-w-[480px]">
                Covenexa brings borrower data, financial documents, covenants, risk signals,
                and AI-powered analysis into one intelligent credit monitoring platform.
              </p>

              {/* CTAs */}
              <div className="flex flex-wrap items-center gap-4">
                {isAuthenticated ? (
                  <Link
                    to="/app"
                    className="inline-flex items-center gap-2 px-6 py-3.5 bg-[#111827] text-white text-sm font-bold rounded-xl hover:bg-[#1F2937] transition-all shadow-lg shadow-[#111827]/20"
                  >
                    Launch Platform
                    <ArrowRight className="w-4 h-4" />
                  </Link>
                ) : (
                  <Link
                    to="/login"
                    className="inline-flex items-center gap-2 px-6 py-3.5 bg-[#111827] text-white text-sm font-bold rounded-xl hover:bg-[#1F2937] transition-all shadow-lg shadow-[#111827]/20"
                  >
                    Get Started
                    <ArrowRight className="w-4 h-4" />
                  </Link>
                )}
                <a
                  href="#capabilities"
                  className="inline-flex items-center gap-2 px-6 py-3.5 border border-[#EEF1F5] bg-white text-sm font-semibold text-[#111827] rounded-xl hover:border-[#7C8DFB]/40 hover:shadow-md transition-all"
                >
                  Explore Platform
                  <ChevronRight className="w-4 h-4 text-[#9CA3AF]" />
                </a>
              </div>

              {/* Social proof */}
              <div className="flex items-center gap-6 pt-2">
                {["AI-Native", "Real-Time", "Evidence-Backed"].map((label) => (
                  <div key={label} className="flex items-center gap-1.5">
                    <CheckCircle2 className="w-3.5 h-3.5 text-[#10B981]" />
                    <span className="text-xs font-medium text-[#6B7280]">{label}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Hero Visual */}
            <div className="relative lg:h-[420px] h-[300px]">
              {/* Outer card */}
              <div className="absolute inset-0 bg-white border border-[#EEF1F5] rounded-3xl shadow-[0_20px_60px_rgba(17,24,39,0.08)] overflow-hidden">
                {/* Card header */}
                <div className="px-5 pt-4 pb-3 border-b border-[#EEF1F5] flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="w-2.5 h-2.5 rounded-full bg-[#EF4444]" />
                    <div className="w-2.5 h-2.5 rounded-full bg-[#F59E0B]" />
                    <div className="w-2.5 h-2.5 rounded-full bg-[#10B981]" />
                  </div>
                  <div className="flex items-center gap-1.5 px-3 py-1 bg-[#F8F9FC] rounded-full border border-[#EEF1F5]">
                    <div className="w-1.5 h-1.5 rounded-full bg-[#10B981] animate-pulse" />
                    <span className="text-[10px] font-semibold text-[#6B7280]">Credit Intelligence Active</span>
                  </div>
                </div>

                {/* Graph area */}
                <div className="relative flex-1 h-[calc(100%-52px)] p-2">
                  <HeroGraph />
                </div>
              </div>

              {/* Floating metric card — bottom left */}
              <div className="absolute -bottom-4 -left-4 bg-white border border-[#EEF1F5] rounded-2xl p-3.5 shadow-dropdown hidden lg:block">
                <p className="text-[10px] font-bold text-[#6B7280] uppercase tracking-wide mb-1">Leverage Ratio</p>
                <p className="text-xl font-black text-[#F97316]">4.1×</p>
                <p className="text-[9px] text-[#10B981] font-semibold mt-0.5">▼ Improving</p>
              </div>

              {/* Floating alert card — top right */}
              <div className="absolute -top-4 -right-4 bg-white border border-[#EEF1F5] rounded-2xl p-3.5 shadow-dropdown hidden lg:block max-w-[160px]">
                <div className="flex items-center gap-1.5 mb-1">
                  <div className="w-1.5 h-1.5 rounded-full bg-[#F97316] animate-pulse" />
                  <span className="text-[10px] font-bold text-[#F97316]">Covenant Alert</span>
                </div>
                <p className="text-[10px] text-[#6B7280] leading-tight">Leverage ratio approaching threshold — 3 days</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── VALUE STRIP ────────────────────────────────────────────────────── */}
      <section className="border-y border-[#EEF1F5] bg-white py-5 overflow-hidden">
        <div className="max-w-7xl mx-auto px-6 lg:px-8">
          <div className="flex flex-wrap justify-center gap-x-10 gap-y-3">
            {valueItems.map((item) => (
              <div key={item} className="flex items-center gap-2 shrink-0">
                <div className="w-1 h-1 rounded-full bg-[#7C8DFB]" />
                <span className="text-xs font-semibold text-[#6B7280]">{item}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── WHAT COVENEXA DOES ──────────────────────────────────────────────── */}
      <section className="py-24 px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <RevealSection className="text-center mb-14">
            <p className="text-xs font-bold text-[#7C8DFB] uppercase tracking-widest mb-3">
              The Platform
            </p>
            <h2 className="text-3xl lg:text-4xl font-black text-[#111827] tracking-tight mb-4">
              One Platform. Complete Credit Intelligence.
            </h2>
            <p className="text-base text-[#6B7280] max-w-xl mx-auto">
              Covenexa connects every layer of credit information into a unified,
              continuously updated intelligence layer.
            </p>
          </RevealSection>

          <RevealSection delay={100}>
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
              {dataConnections.map((dc, i) => {
                const Icon = dc.icon;
                return (
                  <div
                    key={dc.label}
                    className="bg-white border border-[#EEF1F5] rounded-2xl p-5 text-center hover:border-[#7C8DFB]/40 hover:shadow-card transition-all group flex flex-col items-center justify-center"
                    style={{ transitionDelay: `${i * 50}ms` }}
                  >
                    <div
                      className="w-12 h-12 rounded-xl flex items-center justify-center mb-3 transition-transform group-hover:scale-110"
                      style={{ backgroundColor: dc.bg }}
                    >
                      <Icon className="w-6 h-6" style={{ color: dc.color }} />
                    </div>
                    <p className="text-sm font-bold text-[#111827] group-hover:text-[#7C8DFB] transition-colors">
                      {dc.label}
                    </p>
                  </div>
                );
              })}
            </div>
          </RevealSection>
        </div>
      </section>

      {/* ── CORE CAPABILITIES ──────────────────────────────────────────────── */}
      <section id="capabilities" className="py-24 px-6 lg:px-8 bg-white">
        <div className="max-w-7xl mx-auto">
          <RevealSection className="text-center mb-14">
            <p className="text-xs font-bold text-[#7C8DFB] uppercase tracking-widest mb-3">
              Capabilities
            </p>
            <h2 className="text-3xl lg:text-4xl font-black text-[#111827] tracking-tight">
              Built for Credit Intelligence Teams.
            </h2>
          </RevealSection>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-5">
            {capabilities.map((cap, i) => {
              const Icon = cap.icon;
              return (
                <RevealSection key={cap.title} delay={i * 70}>
                  <div className="bg-[#F8F9FC] border border-[#EEF1F5] rounded-2xl p-6 space-y-4 hover:border-[#7C8DFB]/30 hover:shadow-card transition-all h-full">
                    <div
                      style={{ background: cap.bg }}
                      className="w-10 h-10 rounded-xl flex items-center justify-center"
                    >
                      <Icon style={{ color: cap.color }} className="w-5 h-5" />
                    </div>
                    <div>
                      <h3 className="text-sm font-bold text-[#111827] mb-1.5">{cap.title}</h3>
                      <p className="text-xs text-[#6B7280] leading-relaxed">{cap.desc}</p>
                    </div>
                  </div>
                </RevealSection>
              );
            })}
          </div>
        </div>
      </section>

      {/* ── HOW IT WORKS ────────────────────────────────────────────────────── */}
      <section id="how-it-works" className="py-24 px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <RevealSection className="text-center mb-14">
            <p className="text-xs font-bold text-[#7C8DFB] uppercase tracking-widest mb-3">
              Process
            </p>
            <h2 className="text-3xl lg:text-4xl font-black text-[#111827] tracking-tight">
              From Documents to Decisions.
            </h2>
          </RevealSection>

          <div className="grid md:grid-cols-3 gap-6 relative">
            {/* Connector line — desktop */}
            <div className="hidden md:block absolute top-12 left-[22%] right-[22%] h-px bg-gradient-to-r from-[#E8ECFF] via-[#7C8DFB]/40 to-[#E8ECFF]" />

            {steps.map((step, i) => {
              const Icon = step.icon;
              return (
                <RevealSection key={step.num} delay={i * 120}>
                  <div className="text-center space-y-5">
                    <div className="relative inline-flex">
                      <div className="w-24 h-24 rounded-3xl bg-white border border-[#EEF1F5] shadow-card flex items-center justify-center mx-auto">
                        <Icon className="w-10 h-10 text-[#7C8DFB]" />
                      </div>
                      <span className="absolute -top-2 -right-2 w-6 h-6 rounded-full bg-[#111827] text-white text-[10px] font-black flex items-center justify-center">
                        {i + 1}
                      </span>
                    </div>
                    <div>
                      <p className="text-[11px] font-bold text-[#7C8DFB] tracking-widest mb-2">
                        {step.num}
                      </p>
                      <h3 className="text-base font-bold text-[#111827] mb-2">{step.title}</h3>
                      <p className="text-sm text-[#6B7280] leading-relaxed">{step.desc}</p>
                    </div>
                  </div>
                </RevealSection>
              );
            })}
          </div>
        </div>
      </section>

      {/* ── AI / INTELLIGENCE SECTION ─────────────────────────────────────── */}
      <section id="intelligence" className="py-24 px-6 lg:px-8 bg-[#111827]">
        <div className="max-w-7xl mx-auto">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <RevealSection>
              <div className="space-y-6">
                <p className="text-xs font-bold text-[#7C8DFB] uppercase tracking-widest">
                  Intelligence Layer
                </p>
                <h2 className="text-3xl lg:text-4xl font-black text-white leading-tight">
                  Every Answer, Backed by Evidence.
                </h2>
                <p className="text-base text-[#9CA3AF] leading-relaxed">
                  Covenexa doesn't guess. Every insight, recommendation, and risk signal is
                  grounded in real financial data, extracted document text, and connected knowledge
                  — so your team can trust what they act on.
                </p>
                <ul className="space-y-3">
                  {[
                    "Structured financial data from verified sources",
                    "Document intelligence from extracted agreements",
                    "Knowledge graph relationships across borrowers and facilities",
                    "AI reasoning with source citations",
                  ].map((point) => (
                    <li key={point} className="flex items-start gap-3">
                      <CheckCircle2 className="w-4 h-4 text-[#10B981] mt-0.5 shrink-0" />
                      <span className="text-sm text-[#D1D5DB]">{point}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </RevealSection>

            <RevealSection delay={100}>
              {/* Copilot preview card */}
              <div className="bg-[#1F2937] border border-white/10 rounded-3xl p-6 space-y-4">
                <div className="flex items-center gap-2 mb-2">
                  <div className="w-6 h-6 rounded-lg bg-[#7C8DFB]/20 flex items-center justify-center">
                    <Brain className="w-3.5 h-3.5 text-[#7C8DFB]" />
                  </div>
                  <span className="text-xs font-bold text-[#9CA3AF]">AI Credit Copilot</span>
                </div>

                {/* Sample Q&A */}
                {[
                  {
                    q: "What is the maximum leverage ratio permitted in Acme's credit agreement?",
                    a: "The agreement stipulates a maximum Total Leverage Ratio of 4.5× (Total Debt / EBITDA) tested quarterly. Current ratio: 4.1×, representing 9% headroom.",
                    citations: 2,
                  },
                  {
                    q: "Which covenants are approaching their threshold?",
                    a: "Interest Coverage covenant at 1.9× against a minimum of 2.0×. Breach risk within 2 quarters at current trajectory.",
                    citations: 3,
                  },
                ].map((qa, i) => (
                  <div key={i} className="space-y-2">
                    <div className="flex gap-2">
                      <div className="w-5 h-5 rounded-full bg-[#374151] flex items-center justify-center shrink-0 mt-0.5">
                        <span className="text-[9px] font-bold text-[#9CA3AF]">Q</span>
                      </div>
                      <p className="text-xs text-[#D1D5DB] leading-relaxed">{qa.q}</p>
                    </div>
                    <div className="flex gap-2 ml-1">
                      <div className="w-5 h-5 rounded-full bg-[#7C8DFB]/20 flex items-center justify-center shrink-0 mt-0.5">
                        <Brain className="w-2.5 h-2.5 text-[#7C8DFB]" />
                      </div>
                      <div>
                        <p className="text-xs text-[#9CA3AF] leading-relaxed">{qa.a}</p>
                        <p className="text-[10px] text-[#7C8DFB] mt-1">
                          {qa.citations} source citations
                        </p>
                      </div>
                    </div>
                    {i === 0 && <div className="border-t border-white/5 my-2" />}
                  </div>
                ))}
              </div>
            </RevealSection>
          </div>
        </div>
      </section>

      {/* ── SECURITY SECTION ─────────────────────────────────────────────────── */}
      <section id="security" className="py-24 px-6 lg:px-8 bg-white">
        <div className="max-w-7xl mx-auto">
          <RevealSection className="text-center mb-14">
            <p className="text-xs font-bold text-[#7C8DFB] uppercase tracking-widest mb-3">
              Security & Trust
            </p>
            <h2 className="text-3xl lg:text-4xl font-black text-[#111827] tracking-tight mb-4">
              Built for Financial Data.
            </h2>
            <p className="text-base text-[#6B7280] max-w-md mx-auto">
              Covenexa handles sensitive credit information with the controls and auditability
              that institutional lending requires.
            </p>
          </RevealSection>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-5">
            {securityPoints.map((point, i) => {
              const Icon = point.icon;
              return (
                <RevealSection key={point.title} delay={i * 60}>
                  <div className="flex gap-4 p-5 bg-[#F8F9FC] border border-[#EEF1F5] rounded-2xl hover:border-[#7C8DFB]/30 hover:shadow-card transition-all">
                    <div className="w-9 h-9 rounded-xl bg-[#E8ECFF] flex items-center justify-center shrink-0">
                      <Icon className="w-4 h-4 text-[#7C8DFB]" />
                    </div>
                    <div>
                      <h3 className="text-sm font-bold text-[#111827] mb-1">{point.title}</h3>
                      <p className="text-xs text-[#6B7280] leading-relaxed">{point.desc}</p>
                    </div>
                  </div>
                </RevealSection>
              );
            })}
          </div>
        </div>
      </section>

      {/* ── FINAL CTA ──────────────────────────────────────────────────────── */}
      <section className="py-24 px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <RevealSection>
            <div className="bg-[#111827] rounded-3xl px-8 py-16 text-center space-y-8">
              <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-white/10 rounded-full">
                <div className="w-1.5 h-1.5 rounded-full bg-[#10B981] animate-pulse" />
                <span className="text-xs font-bold text-white/60 uppercase tracking-widest">
                  Ready for Production
                </span>
              </div>
              <h2 className="text-3xl lg:text-5xl font-black text-white leading-tight max-w-2xl mx-auto">
                Make Every Credit Decision More Intelligent.
              </h2>
              <p className="text-base text-[#9CA3AF] max-w-md mx-auto">
                Covenexa transforms agreements, financial data, and borrower relationships into
                continuous credit intelligence your team can act on.
              </p>
              <div className="flex flex-wrap justify-center gap-4">
                {isAuthenticated ? (
                  <Link
                    to="/app"
                    className="inline-flex items-center gap-2 px-8 py-4 bg-[#7C8DFB] text-white text-sm font-bold rounded-xl hover:bg-[#6366F1] transition-all shadow-lg shadow-[#7C8DFB]/30"
                  >
                    Launch Platform
                    <ArrowRight className="w-4 h-4" />
                  </Link>
                ) : (
                  <>
                    <Link
                      to="/login"
                      className="inline-flex items-center gap-2 px-8 py-4 bg-[#7C8DFB] text-white text-sm font-bold rounded-xl hover:bg-[#6366F1] transition-all shadow-lg shadow-[#7C8DFB]/30"
                    >
                      Get Started
                      <ArrowRight className="w-4 h-4" />
                    </Link>
                    <Link
                      to="/login"
                      className="inline-flex items-center gap-2 px-8 py-4 bg-white/10 text-white text-sm font-semibold rounded-xl hover:bg-white/15 transition-all border border-white/20"
                    >
                      Sign In
                    </Link>
                  </>
                )}
              </div>
            </div>
          </RevealSection>
        </div>
      </section>

      {/* ── FOOTER ───────────────────────────────────────────────────────────── */}
      <footer className="border-t border-[#EEF1F5] bg-white py-10 px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-8">
            {/* Brand */}
            <div className="space-y-3">
              <Link to="/" className="flex items-center gap-2.5">
                <CovLogo size={28} />
                <span className="text-base font-bold text-[#111827]">Covenexa</span>
              </Link>
              <p className="text-xs text-[#6B7280] max-w-xs leading-relaxed">
                AI-native credit intelligence platform for modern lending and risk teams.
              </p>
            </div>

            {/* Links */}
            <div className="grid grid-cols-2 gap-x-12 gap-y-2">
              {[
                { label: "Platform", href: "#capabilities" },
                { label: "How It Works", href: "#how-it-works" },
                { label: "Security", href: "#security" },
                { label: "Login", href: "/login" },
              ].map((link) => (
                <a
                  key={link.label}
                  href={link.href}
                  className="text-xs text-[#6B7280] hover:text-[#111827] transition-colors"
                >
                  {link.label}
                </a>
              ))}
            </div>
          </div>

          <div className="mt-10 pt-6 border-t border-[#EEF1F5] flex flex-col sm:flex-row items-center justify-between gap-3">
            <p className="text-xs text-[#9CA3AF]">
              © 2026 Covenexa. Credit Risk Intelligence Platform.
            </p>
            <div className="flex items-center gap-4">
              <a href="#" className="text-xs text-[#9CA3AF] hover:text-[#6B7280] transition-colors">Privacy</a>
              <a href="#" className="text-xs text-[#9CA3AF] hover:text-[#6B7280] transition-colors">Terms</a>
              <a href="#" className="text-xs text-[#9CA3AF] hover:text-[#6B7280] transition-colors">Contact</a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
