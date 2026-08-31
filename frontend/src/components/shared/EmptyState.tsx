import React from "react";
import { LucideIcon, FileX2 } from "lucide-react";

interface EmptyStateProps {
  title: string;
  description: string;
  actionText?: string;
  onAction?: () => void;
  icon?: LucideIcon;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title,
  description,
  actionText,
  onAction,
  icon: Icon = FileX2,
}) => {
  return (
    <div className="bg-white rounded-2xl p-12 border border-[#EEF1F5] text-center flex flex-col items-center justify-center my-4 shadow-[0_4px_20px_rgba(17,24,39,0.02)]">
      <div className="w-14 h-14 rounded-full bg-[#F3F4FF] text-[#7C8DFB] flex items-center justify-center mb-4">
        <Icon className="w-7 h-7" />
      </div>
      <h3 className="text-base font-bold text-[#111827]">{title}</h3>
      <p className="text-xs text-[#6B7280] max-w-sm mt-1 mb-6 leading-relaxed">
        {description}
      </p>
      {actionText && onAction && (
        <button
          onClick={onAction}
          className="px-4 py-2.5 bg-[#7C8DFB] hover:bg-[#6366F1] text-white font-semibold rounded-xl text-xs shadow-sm transition-all"
        >
          {actionText}
        </button>
      )}
    </div>
  );
};
