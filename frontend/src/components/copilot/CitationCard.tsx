import React, { useState } from "react";
import { Database, Search, Network, FileText, ChevronDown, ChevronUp } from "lucide-react";
import { NormalizedEvidence } from "@/utils/normalizeEvidence";

interface CitationCardProps {
  evidence: NormalizedEvidence;
  index: number;
}

export const CitationCard: React.FC<CitationCardProps> = ({ evidence, index }) => {
  const [expanded, setExpanded] = useState(false);

  const isFinancial = evidence.type === "financial";
  const isDocument = evidence.type === "document";
  const isGraph = evidence.type === "knowledge_graph";

  const Icon = isFinancial
    ? Database
    : isDocument
    ? Search
    : isGraph
    ? Network
    : FileText;

  const iconColor = isFinancial
    ? "text-emerald-600"
    : isDocument
    ? "text-indigo-600"
    : isGraph
    ? "text-amber-600"
    : "text-gray-600";

  if (!evidence.available) {
    return (
      <div className="p-3 rounded-xl border border-[#EEF1F5] bg-[#F8F9FC]/60 space-y-1.5 transition-all text-xs opacity-75">
        <div className="flex items-center justify-between gap-1.5">
          <div className="flex items-center gap-1.5">
            <Icon className={`w-3.5 h-3.5 ${iconColor}`} />
            <span className="font-semibold text-[#6B7280] text-[11px]">
              {evidence.label}
            </span>
          </div>
          <span className="text-[9px] font-medium text-[#9CA3AF] bg-[#EEF1F5] px-1.5 py-0.5 rounded">
            Unavailable
          </span>
        </div>
        <p className="text-[11px] text-[#6B7280] italic leading-relaxed pl-5">
          {evidence.items[0] || "No records available for this query."}
        </p>
      </div>
    );
  }

  return (
    <div className="p-3.5 rounded-xl border border-[#EEF1F5] bg-white hover:border-[#7C8DFB]/30 hover:shadow-xs transition-all space-y-2 text-xs">
      {/* Header */}
      <div className="flex items-center justify-between gap-1.5">
        <div className="flex items-center gap-1.5">
          <Icon className={`w-3.5 h-3.5 ${iconColor}`} />
          <span className="font-bold text-[#111827] text-[11px]">
            {evidence.label}
          </span>
          {evidence.page && (
            <span className="text-[10px] font-medium text-indigo-700 bg-indigo-50 border border-indigo-100 px-1.5 py-0.2 rounded-md">
              p. {evidence.page}
            </span>
          )}
          {evidence.section && (
            <span className="text-[10px] font-medium text-gray-600 bg-gray-100 px-1.5 py-0.2 rounded-md">
              {evidence.section}
            </span>
          )}
        </div>
        <span className="text-[10px] font-mono text-[#9CA3AF]">
          #{index + 1}
        </span>
      </div>

      {/* Structured Key-Value / Metrics for Financial Data */}
      {isFinancial && evidence.items.length > 0 && (
        <div className="grid grid-cols-1 gap-1 pl-5">
          {evidence.items.map((item, i) => {
            const [k, ...rest] = item.split(":");
            const v = rest.join(":").trim();
            if (v) {
              return (
                <div key={i} className="flex items-baseline justify-between text-[11px] py-0.5 border-b border-[#F8F9FC] last:border-0">
                  <span className="text-[#6B7280] font-medium">{k.trim()}</span>
                  <span className="text-[#111827] font-semibold">{v}</span>
                </div>
              );
            }
            return (
              <p key={i} className="text-[11px] text-[#374151] leading-relaxed">
                • {item}
              </p>
            );
          })}
        </div>
      )}

      {/* Document Reference / Excerpt */}
      {isDocument && (
        <div className="pl-5 space-y-1.5">
          {evidence.documentName && (
            <div className="flex items-center gap-1.5 text-[11px] font-semibold text-[#111827]">
              <FileText className="w-3.5 h-3.5 text-[#4F46E5] shrink-0" />
              <span>{evidence.documentName}</span>
            </div>
          )}

          {evidence.pages && evidence.pages.length > 0 && (
            <div className="flex flex-wrap items-center gap-1 text-[10px] text-[#6B7280]">
              <span className="font-medium text-[#4B5563]">Referenced pages:</span>
              {evidence.pages.map((p, pIdx) => (
                <span
                  key={pIdx}
                  className="px-1.5 py-0.2 bg-indigo-50 text-indigo-700 font-semibold rounded border border-indigo-100"
                >
                  p. {p}
                </span>
              ))}
            </div>
          )}

          {evidence.excerpt && (
            <div>
              <p
                className={`text-[11px] text-[#4B5563] leading-relaxed italic ${
                  !expanded ? "line-clamp-3" : ""
                }`}
              >
                "{evidence.excerpt}"
              </p>
              {evidence.excerpt.length > 180 && (
                <button
                  onClick={() => setExpanded(!expanded)}
                  className="text-[10px] text-[#4F46E5] hover:underline font-medium flex items-center gap-0.5 mt-1"
                >
                  {expanded ? (
                    <>
                      Show less <ChevronUp className="w-3 h-3" />
                    </>
                  ) : (
                    <>
                      Read full excerpt <ChevronDown className="w-3 h-3" />
                    </>
                  )}
                </button>
              )}
            </div>
          )}
        </div>
      )}

      {/* Knowledge Graph Relations */}
      {isGraph && evidence.items.length > 0 && (
        <div className="pl-5 space-y-1">
          {evidence.items.map((rel, i) => (
            <div
              key={i}
              className="p-1.5 rounded bg-[#F8F9FC] border border-[#EEF1F5] text-[11px] font-mono text-[#1F2937]"
            >
              {rel}
            </div>
          ))}
        </div>
      )}

      {/* Generic fallback */}
      {evidence.type === "generic" && (
        <div className="pl-5">
          {evidence.items.map((it, i) => (
            <p key={i} className="text-[11px] text-[#374151] leading-relaxed">
              {it}
            </p>
          ))}
        </div>
      )}
    </div>
  );
};

export default CitationCard;
