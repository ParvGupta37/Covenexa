import React from "react";
import { LucideIcon } from "lucide-react";
import { ResponsiveContainer, LineChart, Line } from "recharts";
import { InfoTooltip } from "@/components/shared/Explainer";

interface KpiCardProps {
  title: string;
  /** Short plain-language description of what this metric measures */
  subtitle?: string;
  /** Tooltip shown on the info icon */
  tooltip?: string;
  value: string | number;
  badgeText?: string;
  badgeType?: "watch" | "danger" | "success" | "warning" | "neutral";
  trendText?: string;
  trendUp?: boolean;
  icon: LucideIcon;
  iconBgColor?: string;
  iconColor?: string;
  sparklineData?: number[];
}

export const KpiCard: React.FC<KpiCardProps> = ({
  title,
  subtitle,
  tooltip,
  value,
  badgeText,
  badgeType = "neutral",
  trendText,
  trendUp = true,
  icon: Icon,
  iconBgColor = "#E8ECFF",
  iconColor = "#7C8DFB",
  sparklineData,
}) => {
  const getBadgeStyle = () => {
    switch (badgeType) {
      case "watch":
        return "bg-[#E8ECFF] text-[#4F46E5]";
      case "danger":
        return "bg-[#FEE2E2] text-[#EF4444]";
      case "warning":
        return "bg-[#FFEDD5] text-[#F97316]";
      case "success":
        return "bg-[#D1FAE5] text-[#10B981]";
      default:
        return "bg-gray-100 text-gray-700";
    }
  };

  const formattedSparkline = sparklineData?.map((val, idx) => ({ val, idx }));

  return (
    <div className="bg-white rounded-2xl p-5 border border-[#EEF1F5] shadow-[0_4px_20px_rgba(17,24,39,0.04)] flex flex-col justify-between hover:shadow-[0_8px_30px_rgba(17,24,39,0.07)] transition-all">
      {/* Top Header */}
      <div className="flex items-center gap-3">
        <div
          className="w-10 h-10 rounded-full flex items-center justify-center shrink-0"
          style={{ backgroundColor: iconBgColor, color: iconColor }}
        >
          <Icon className="w-5 h-5" />
        </div>
        <div className="min-w-0">
          <div className="flex items-center gap-0.5">
            <span className="text-sm font-semibold text-[#6B7280] leading-tight">{title}</span>
            {tooltip && <InfoTooltip text={tooltip} />}
          </div>
          {subtitle && (
            <p className="text-[10px] text-[#9CA3AF] mt-0.5 leading-tight">{subtitle}</p>
          )}
        </div>
      </div>

      {/* Main Metric Value & Badges */}
      <div className="mt-4 flex items-baseline justify-between gap-2">
        <div className="flex items-baseline gap-2 flex-wrap">
          <span className="text-3xl font-bold text-[#111827] tracking-tight">{value}</span>
          {badgeText && (
            <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold ${getBadgeStyle()}`}>
              {badgeText}
            </span>
          )}
        </div>

        {trendText && (
          <div className="flex items-center gap-1 text-xs font-semibold text-[#6B7280] shrink-0">
            <span className={trendUp ? "text-[#EF4444]" : "text-[#10B981]"}>
              {trendUp ? "▲" : "▼"} {trendText}
            </span>
          </div>
        )}
      </div>

      {/* Mini Sparkline Chart */}
      {formattedSparkline && formattedSparkline.length > 0 && (
        <div className="h-8 mt-3 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={formattedSparkline}>
              <Line
                type="monotone"
                dataKey="val"
                stroke={iconColor}
                strokeWidth={2}
                dot={false}
                isAnimationActive={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
};
