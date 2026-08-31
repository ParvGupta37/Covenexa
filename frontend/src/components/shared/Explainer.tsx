/**
 * Shared explainability components for Covenexa analyst UX.
 * Provides lightweight tooltips, info icons, contextual banners,
 * 3-part analyst cards (What is it? Why does it matter? What should I do?),
 * and empty state helpers without heavy external dependencies.
 */
import { useState, useRef, useEffect } from "react";
import { Info, HelpCircle } from "lucide-react";
import type { LucideIcon } from "lucide-react";

// ─── InfoTooltip ──────────────────────────────────────────────────────────────
// Tiny info icon that reveals a tooltip on hover.
interface InfoTooltipProps {
  text: string;
  /** optional link label */
  size?: "sm" | "md";
}

export function InfoTooltip({ text, size = "sm" }: InfoTooltipProps) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  // Close on outside click
  useEffect(() => {
    function handler(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    if (open) document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [open]);

  return (
    <div ref={ref} className="relative inline-flex items-center" style={{ verticalAlign: "middle" }}>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        onMouseEnter={() => setOpen(true)}
        onMouseLeave={() => setOpen(false)}
        className={`text-[#9CA3AF] hover:text-[#7C8DFB] transition-colors focus:outline-none ${
          size === "md" ? "ml-1.5" : "ml-1"
        }`}
        aria-label="More information"
      >
        <Info className={size === "md" ? "w-3.5 h-3.5" : "w-3 h-3"} />
      </button>

      {open && (
        <div
          role="tooltip"
          className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 z-50 w-56 bg-[#111827] text-white text-[11px] leading-relaxed font-normal rounded-xl px-3 py-2.5 shadow-xl pointer-events-none"
        >
          {text}
          {/* arrow */}
          <span className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-[#111827]" />
        </div>
      )}
    </div>
  );
}

// ─── ContextBanner ────────────────────────────────────────────────────────────
// A compact informational callout at the top of a page/section.
interface ContextBannerProps {
  icon?: LucideIcon;
  title: string;
  description: string;
  /** Optional expandable "Learn more" content */
  learnMore?: string;
}

export function ContextBanner({
  icon: Icon = HelpCircle,
  title,
  description,
  learnMore,
}: ContextBannerProps) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="flex gap-3 p-4 bg-[#F8F9FC] border border-[#EEF1F5] rounded-2xl">
      <div className="w-8 h-8 rounded-xl bg-[#E8ECFF] flex items-center justify-center shrink-0 mt-0.5">
        <Icon className="w-4 h-4 text-[#7C8DFB]" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-xs font-bold text-[#111827]">{title}</p>
        <p className="text-xs text-[#6B7280] mt-0.5 leading-relaxed">{description}</p>
        {learnMore && (
          <>
            <button
              type="button"
              onClick={() => setExpanded((v) => !v)}
              className="text-[11px] font-semibold text-[#7C8DFB] hover:text-[#4F46E5] mt-1.5 transition-colors"
            >
              {expanded ? "Show less ↑" : "Learn more ↓"}
            </button>
            {expanded && (
              <p className="text-[11px] text-[#6B7280] mt-1.5 leading-relaxed border-t border-[#EEF1F5] pt-1.5">
                {learnMore}
              </p>
            )}
          </>
        )}
      </div>
    </div>
  );
}

// ─── AnalystExplainerCard ──────────────────────────────────────────────────────
// Part 4 Pattern: 3-part card answering WHAT IS IT? WHY DOES IT MATTER? WHAT SHOULD I DO?
interface AnalystExplainerCardProps {
  title: string;
  whatIsIt: string;
  whyItMatters: string;
  whatShouldIDo: string;
}

export function AnalystExplainerCard({
  title,
  whatIsIt,
  whyItMatters,
  whatShouldIDo,
}: AnalystExplainerCardProps) {
  return (
    <div className="p-4 bg-[#F8F9FC] border border-[#EEF1F5] rounded-2xl space-y-3">
      <h4 className="text-xs font-bold text-[#111827] uppercase tracking-wider border-b border-[#EEF1F5] pb-2">
        {title} — Analyst Guidance
      </h4>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
        <div>
          <span className="text-[10px] font-bold uppercase tracking-wide text-[#7C8DFB] block">What is it?</span>
          <p className="text-[#6B7280] mt-0.5 leading-relaxed">{whatIsIt}</p>
        </div>
        <div>
          <span className="text-[10px] font-bold uppercase tracking-wide text-[#F97316] block">Why does it matter?</span>
          <p className="text-[#6B7280] mt-0.5 leading-relaxed">{whyItMatters}</p>
        </div>
        <div>
          <span className="text-[10px] font-bold uppercase tracking-wide text-[#10B981] block">What should I do?</span>
          <p className="text-[#6B7280] mt-0.5 leading-relaxed">{whatShouldIDo}</p>
        </div>
      </div>
    </div>
  );
}

// ─── SectionLabel ─────────────────────────────────────────────────────────────
// Section heading with an optional tooltip.
interface SectionLabelProps {
  children: React.ReactNode;
  tooltip?: string;
  className?: string;
}

export function SectionLabel({ children, tooltip, className = "" }: SectionLabelProps) {
  return (
    <span className={`inline-flex items-center gap-0.5 ${className}`}>
      {children}
      {tooltip && <InfoTooltip text={tooltip} />}
    </span>
  );
}

// ─── MetricExplainer ─────────────────────────────────────────────────────────
// A single metric row with label + value + inline explanation tooltip.
interface MetricExplainerProps {
  label: string;
  value: React.ReactNode;
  tooltip: string;
  valueClassName?: string;
}

export function MetricExplainer({ label, value, tooltip, valueClassName = "" }: MetricExplainerProps) {
  return (
    <div className="flex items-center justify-between py-2.5 border-b border-[#EEF1F5] last:border-0">
      <span className="flex items-center gap-0.5 text-xs text-[#6B7280] font-medium">
        {label}
        <InfoTooltip text={tooltip} />
      </span>
      <span className={`text-xs font-bold text-[#111827] ${valueClassName}`}>{value}</span>
    </div>
  );
}

// ─── ImprovedEmptyState ───────────────────────────────────────────────────────
// Richer empty states with action guidance.
interface ImprovedEmptyStateProps {
  icon: LucideIcon;
  title: string;
  description: string;
  /** Optional call-to-action button */
  actionLabel?: string;
  onAction?: () => void;
}

export function ImprovedEmptyState({
  icon: Icon,
  title,
  description,
  actionLabel,
  onAction,
}: ImprovedEmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <div className="w-14 h-14 rounded-2xl bg-[#E8ECFF] flex items-center justify-center mb-4">
        <Icon className="w-7 h-7 text-[#7C8DFB]" />
      </div>
      <h3 className="text-sm font-bold text-[#111827] mb-1">{title}</h3>
      <p className="text-xs text-[#6B7280] leading-relaxed max-w-xs">{description}</p>
      {actionLabel && onAction && (
        <button
          onClick={onAction}
          className="mt-4 px-4 py-2 bg-[#7C8DFB] text-white text-xs font-semibold rounded-xl hover:bg-[#6366F1] transition-all"
        >
          {actionLabel}
        </button>
      )}
    </div>
  );
}

// ─── CovenantStatusGuide ──────────────────────────────────────────────────────
// Small inline legend explaining covenant status values.
export function CovenantStatusGuide() {
  return (
    <div className="flex flex-wrap gap-2 text-[10px]">
      {[
        { label: "Compliant", color: "bg-[#D1FAE5] text-[#059669]", desc: "Within threshold" },
        { label: "Warning", color: "bg-[#FFEDD5] text-[#EA580C]", desc: "Approaching limit" },
        { label: "Breached", color: "bg-[#FEE2E2] text-[#DC2626]", desc: "Threshold exceeded" },
        { label: "Not Monitored", color: "bg-[#F3F4F6] text-[#6B7280]", desc: "No tracking active" },
      ].map((s) => (
        <span key={s.label} className={`px-2 py-0.5 rounded-full font-semibold ${s.color}`} title={s.desc}>
          {s.label}
        </span>
      ))}
    </div>
  );
}
