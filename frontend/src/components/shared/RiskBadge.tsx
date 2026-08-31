import React from "react";

interface RiskBadgeProps {
  category?: string | null;
  className?: string;
}

export const RiskBadge: React.FC<RiskBadgeProps> = ({ category, className = "" }) => {
  if (!category) {
    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-500 ${className}`}>
        UNANALYZED
      </span>
    );
  }

  const normalized = category.toUpperCase().replace(/\s+/g, "_");

  if (normalized.includes("HIGH") || normalized.includes("CRITICAL")) {
    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-[#FEE2E2] text-[#EF4444] ${className}`}>
        High Risk
      </span>
    );
  }

  if (normalized.includes("WATCH") || normalized.includes("ELEVATED")) {
    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-[#FFEDD5] text-[#F97316] ${className}`}>
        Watch
      </span>
    );
  }

  if (normalized.includes("MODERATE") || normalized.includes("MEDIUM")) {
    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-[#FEF3C7] text-[#D97706] ${className}`}>
        Moderate
      </span>
    );
  }

  if (normalized.includes("LOW") || normalized.includes("GOOD") || normalized.includes("HEALTHY") || normalized.includes("EXCELLENT")) {
    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-[#D1FAE5] text-[#10B981] ${className}`}>
        Low Risk
      </span>
    );
  }

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-700 ${className}`}>
      {category}
    </span>
  );
};
