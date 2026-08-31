import React from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface MarkdownRendererProps {
  content: string;
  className?: string;
}

export const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({
  content,
  className = "",
}) => {
  if (!content || !content.trim()) {
    return <span className="text-[#9CA3AF] italic">No content</span>;
  }

  return (
    <div className={`copilot-markdown leading-relaxed space-y-1 text-xs md:text-[13px] ${className}`}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          h1: ({ children }) => (
            <h1 className="text-sm md:text-base font-bold text-[#111827] mt-3 mb-1.5 pb-1 border-b border-[#EEF1F5]">
              {children}
            </h1>
          ),
          h2: ({ children }) => (
            <h2 className="text-xs md:text-sm font-bold text-[#111827] mt-2.5 mb-1">
              {children}
            </h2>
          ),
          h3: ({ children }) => (
            <h3 className="text-xs md:text-[13px] font-semibold text-[#1F2937] mt-2 mb-0.5">
              {children}
            </h3>
          ),
          h4: ({ children }) => (
            <h4 className="text-xs font-semibold text-[#374151] mt-1.5 mb-0.5">
              {children}
            </h4>
          ),
          p: ({ children }) => (
            <p className="mb-2 last:mb-0 leading-relaxed text-[#1F2937]">
              {children}
            </p>
          ),
          strong: ({ children }) => (
            <strong className="font-bold text-[#111827]">{children}</strong>
          ),
          em: ({ children }) => (
            <em className="italic text-[#374151]">{children}</em>
          ),
          ul: ({ children }) => (
            <ul className="list-disc list-outside pl-4 space-y-1 mb-2.5 text-[#1F2937]">
              {children}
            </ul>
          ),
          ol: ({ children }) => (
            <ol className="list-decimal list-outside pl-4 space-y-1 mb-2.5 text-[#1F2937]">
              {children}
            </ol>
          ),
          li: ({ children }) => (
            <li className="leading-relaxed pl-0.5">{children}</li>
          ),
          blockquote: ({ children }) => (
            <blockquote className="border-l-2 border-[#7C8DFB] pl-3 py-0.5 italic text-[#4B5563] my-2 bg-[#F8F9FC] rounded-r">
              {children}
            </blockquote>
          ),
          code: ({ children, className }) => {
            const isInline = !className;
            return isInline ? (
              <code className="bg-[#EEF2F6] text-[#4F46E5] px-1.5 py-0.5 rounded text-[11px] font-mono">
                {children}
              </code>
            ) : (
              <code className="block bg-[#1E293B] text-[#F8FAFC] p-3 rounded-lg overflow-x-auto text-[11px] font-mono my-2">
                {children}
              </code>
            );
          },
          table: ({ children }) => (
            <div className="overflow-x-auto my-2 rounded-lg border border-[#EEF1F5]">
              <table className="min-w-full divide-y divide-[#EEF1F5] text-[11px]">
                {children}
              </table>
            </div>
          ),
          thead: ({ children }) => (
            <thead className="bg-[#F8F9FC] text-[#111827]">{children}</thead>
          ),
          tbody: ({ children }) => (
            <tbody className="divide-y divide-[#EEF1F5] bg-white">{children}</tbody>
          ),
          th: ({ children }) => (
            <th className="px-3 py-1.5 text-left font-semibold text-[#111827]">
              {children}
            </th>
          ),
          td: ({ children }) => (
            <td className="px-3 py-1.5 text-[#374151] whitespace-nowrap">
              {children}
            </td>
          ),
          a: ({ href, children }) => (
            <a
              href={href}
              target="_blank"
              rel="noopener noreferrer"
              className="text-[#4F46E5] hover:underline font-medium"
            >
              {children}
            </a>
          ),
          hr: () => <hr className="my-3 border-[#EEF1F5]" />,
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
};

export default MarkdownRenderer;
