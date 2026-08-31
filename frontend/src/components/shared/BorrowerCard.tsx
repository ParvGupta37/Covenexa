import React from "react";
import { BorrowerAvatar } from "./BorrowerAvatar";
import { RiskBadge } from "./RiskBadge";
import { ChevronRight } from "lucide-react";

interface BorrowerCardProps {
  id?: string;
  name: string;
  score?: number | null;
  category?: string | null;
  onClick?: () => void;
}

export const BorrowerCard: React.FC<BorrowerCardProps> = ({
  name,
  score,
  category,
  onClick,
}) => {
  return (
    <div
      onClick={onClick}
      className="bg-white rounded-2xl p-4 border border-[#EEF1F5] shadow-[0_4px_20px_rgba(17,24,39,0.03)] hover:shadow-[0_8px_30px_rgba(17,24,39,0.07)] transition-all cursor-pointer flex flex-col justify-between"
    >
      <div className="flex items-center gap-3">
        <BorrowerAvatar name={name} size="md" />
        <div className="flex-1 min-w-0">
          <h4 className="text-sm font-bold text-[#111827] truncate">{name}</h4>
          <span className="text-xs text-[#6B7280]">Borrower Profile</span>
        </div>
        <ChevronRight className="w-4 h-4 text-gray-400 shrink-0" />
      </div>

      <div className="mt-4 pt-3 border-t border-[#F3F4F6] flex items-center justify-between">
        <div className="flex items-baseline gap-1">
          <span className="text-2xl font-bold text-[#111827]">
            {score !== null && score !== undefined ? score.toFixed(1) : "N/A"}
          </span>
          <span className="text-xs text-gray-400">/100</span>
        </div>
        <RiskBadge category={category} />
      </div>
    </div>
  );
};
