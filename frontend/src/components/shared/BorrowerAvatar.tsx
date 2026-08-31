import React from "react";

interface BorrowerAvatarProps {
  name: string;
  size?: "sm" | "md" | "lg";
  className?: string;
}

const PASTEL_COLORS = [
  { bg: "#FEE2E2", text: "#EF4444" },
  { bg: "#FFEDD5", text: "#F97316" },
  { bg: "#FEF3C7", text: "#D97706" },
  { bg: "#D1FAE5", text: "#10B981" },
  { bg: "#E8ECFF", text: "#4F46E5" },
  { bg: "#F3E8FF", text: "#9333EA" },
];

export const BorrowerAvatar: React.FC<BorrowerAvatarProps> = ({ name, size = "md", className = "" }) => {
  const getInitials = (n: string) => {
    const parts = n.trim().split(/\s+/);
    if (parts.length >= 2) {
      return (parts[0][0] + parts[1][0]).toUpperCase();
    }
    return n.slice(0, 2).toUpperCase();
  };

  const initials = getInitials(name || "Borrower");
  const charCodeSum = name ? name.split("").reduce((acc, char) => acc + char.charCodeAt(0), 0) : 0;
  const colorScheme = PASTEL_COLORS[charCodeSum % PASTEL_COLORS.length];

  const sizeClasses = {
    sm: "w-8 h-8 text-xs font-bold rounded-full",
    md: "w-11 h-11 text-sm font-bold rounded-2xl",
    lg: "w-14 h-14 text-base font-bold rounded-2xl",
  };

  return (
    <div
      className={`flex items-center justify-center font-semibold tracking-wider shrink-0 transition-transform ${sizeClasses[size]} ${className}`}
      style={{ backgroundColor: colorScheme.bg, color: colorScheme.text }}
    >
      {initials}
    </div>
  );
};
