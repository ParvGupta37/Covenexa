import React from "react";
import { Sparkles, ArrowRight } from "lucide-react";

interface InsightCardProps {
  title?: string;
  insight: string;
  onAskCopilot?: () => void;
  className?: string;
}

export const InsightCard: React.FC<InsightCardProps> = ({
  title = "AI Insight",
  insight,
  onAskCopilot,
  className = "",
}) => {
  return (
    <div
      className={`bg-white rounded-2xl p-5 border border-[#EEF1F5] shadow-[0_4px_20px_rgba(17,24,39,0.04)] flex flex-col justify-between ${className}`}
    >
      <div>
        <div className="flex items-center gap-2 text-[#7C8DFB] mb-3">
          <Sparkles className="w-4 h-4" />
          <span className="text-xs font-bold uppercase tracking-wider">{title}</span>
        </div>
        <p className="text-sm text-[#111827] font-medium leading-relaxed">
          {insight}
        </p>
      </div>

      <div className="mt-5 flex justify-end">
        <button
          onClick={onAskCopilot}
          className="flex items-center gap-1.5 px-4 py-2 bg-[#7C8DFB] hover:bg-[#6366F1] text-white rounded-xl text-xs font-semibold shadow-sm transition-all"
        >
          <span>Ask Copilot</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  );
};
