import React from "react";

interface StatusBadgeProps {
  status?: string | null;
  className?: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, className = "" }) => {
  if (!status) {
    return (
      <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-500 ${className}`}>
        N/A
      </span>
    );
  }

  const s = status.toLowerCase();

  if (s === "compliant" || s === "healthy" || s === "processed" || s === "active" || s === "done") {
    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-[#D1FAE5] text-[#10B981] ${className}`}>
        {status.toUpperCase()}
      </span>
    );
  }

  if (s === "breach" || s === "critical" || s === "failed" || s === "defaulted" || s === "overdue") {
    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-[#FEE2E2] text-[#EF4444] ${className}`}>
        {status.toUpperCase()}
      </span>
    );
  }

  if (s === "warning" || s === "at_risk" || s === "pending" || s === "processing") {
    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-[#FFEDD5] text-[#F97316] ${className}`}>
        {status.toUpperCase()}
      </span>
    );
  }

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-700 ${className}`}>
      {status}
    </span>
  );
};
