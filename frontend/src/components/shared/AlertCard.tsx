import React from "react";
import { AlertTriangle, AlertCircle, Clock } from "lucide-react";

interface AlertCardProps {
  title: string;
  borrowerName?: string;
  timeAgo?: string;
  severity?: "critical" | "warning" | "info" | string;
  message?: string;
}

export const AlertCard: React.FC<AlertCardProps> = ({
  title,
  borrowerName = "Portfolio Company",
  timeAgo = "Recently",
  severity = "warning",
}) => {
  const isCritical = severity?.toLowerCase() === "critical" || severity?.toLowerCase() === "high";

  return (
    <div className="flex items-start gap-3 p-3 rounded-xl hover:bg-[#F8F9FC] transition-colors border border-transparent hover:border-[#EEF1F5]">
      <div
        className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 mt-0.5 ${
          isCritical
            ? "bg-[#FEE2E2] text-[#EF4444]"
            : "bg-[#FFEDD5] text-[#F97316]"
        }`}
      >
        {isCritical ? (
          <AlertTriangle className="w-4 h-4" />
        ) : (
          <AlertCircle className="w-4 h-4" />
        )}
      </div>

      <div className="flex-1 min-w-0">
        <h4 className="text-xs font-semibold text-[#111827] truncate">{title}</h4>
        <p className="text-xs text-[#6B7280] truncate mt-0.5">{borrowerName}</p>
      </div>

      <div className="flex items-center gap-1 text-[11px] text-[#9CA3AF] shrink-0">
        <Clock className="w-3 h-3" />
        <span>{timeAgo}</span>
      </div>
    </div>
  );
};
