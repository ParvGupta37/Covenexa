import React from "react";

export const CardSkeleton: React.FC<{ height?: string }> = ({ height = "h-32" }) => (
  <div className={`bg-white rounded-2xl p-5 border border-[#EEF1F5] animate-pulse ${height}`}>
    <div className="flex items-center gap-3">
      <div className="w-10 h-10 rounded-full bg-gray-200" />
      <div className="h-4 bg-gray-200 rounded w-1/3" />
    </div>
    <div className="mt-4 h-8 bg-gray-200 rounded w-1/2" />
  </div>
);

export const TableRowSkeleton: React.FC<{ cols?: number }> = ({ cols = 5 }) => (
  <tr className="animate-pulse border-b border-gray-100">
    {Array.from({ length: cols }).map((_, idx) => (
      <td key={idx} className="py-4 px-4">
        <div className="h-4 bg-gray-200 rounded w-3/4" />
      </td>
    ))}
  </tr>
);
