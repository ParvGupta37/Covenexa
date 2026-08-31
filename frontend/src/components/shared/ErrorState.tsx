import React from "react";
import { AlertTriangle, RefreshCw } from "lucide-react";

interface ErrorStateProps {
  title?: string;
  message?: string;
  onRetry?: () => void;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  title = "Something went wrong",
  message = "We couldn't load this information right now. Please try again.",
  onRetry,
}) => {
  return (
    <div className="bg-white rounded-2xl p-8 border border-[#FCA5A5]/30 bg-[#FEE2E2]/10 text-center flex flex-col items-center justify-center my-4">
      <div className="w-12 h-12 rounded-full bg-[#FEE2E2] text-[#EF4444] flex items-center justify-center mb-3">
        <AlertTriangle className="w-6 h-6" />
      </div>
      <h3 className="text-sm font-bold text-[#111827]">{title}</h3>
      <p className="text-xs text-[#6B7280] max-w-sm mt-1 mb-4">
        {message}
      </p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="flex items-center gap-1.5 px-4 py-2 bg-white hover:bg-gray-50 border border-gray-200 text-[#111827] font-medium rounded-xl text-xs shadow-sm transition-all"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Retry</span>
        </button>
      )}
    </div>
  );
};
