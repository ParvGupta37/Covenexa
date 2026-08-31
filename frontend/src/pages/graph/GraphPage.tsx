import { useState, useEffect } from "react";
import { Info, Loader2, Network } from "lucide-react";
import api from "@/lib/api";
import { useCompanyStore } from "@/store/company.store";


interface NodeItem {
  id: string;
  label: string;
  type: "borrower" | "loan" | "agreement" | "covenant" | "financial";
  details: string;
  x: number;
  y: number;
}

interface EdgeItem {
  from: string;
  to: string;
}

const TYPE_COLORS: Record<string, string> = {
  borrower: "#10B981",
  loan: "#7C8DFB",
  agreement: "#9333EA",
  covenant: "#F59E0B",
  financial: "#EF4444",
};

// Node type descriptions for the inspector
const TYPE_DESCRIPTIONS: Record<string, string> = {
  borrower: "The company or entity that has taken on credit obligations. The central entity in any credit relationship.",
  loan: "A credit facility — the specific loan or revolving credit agreement between the lender and borrower.",
  agreement: "The legal document governing loan terms, including covenants, repayment schedule, and financial maintenance requirements.",
  covenant: "A financial condition the borrower must continuously satisfy under the credit agreement (e.g., maintain leverage below 4.5×).",
  financial: "Extracted financial data from borrower statements — including ratios, revenue, EBITDA, and debt metrics.",
};

export default function GraphPage() {
  const { selectedCompanyId, selectedCompany } = useCompanyStore();
  const selectedBorrowerId = selectedCompanyId;

  const [nodes, setNodes] = useState<NodeItem[]>([]);
  const [edges, setEdges] = useState<EdgeItem[]>([]);
  const [selectedNode, setSelectedNode] = useState<NodeItem | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!selectedBorrowerId) return;
    async function loadGraph() {
      setLoading(true);
      try {
        const res = await api.get(`/api/v1/risk/graph/${selectedBorrowerId}`);
        if (res.data) {
          setNodes(res.data.nodes || []);
          setEdges(res.data.edges || []);
          if (res.data.nodes && res.data.nodes.length > 0) {
            setSelectedNode(res.data.nodes[0]);
          } else {
            setSelectedNode(null);
          }
        }
      } catch (e) {
        console.error("Failed to load graph data", e);
      } finally {
        setLoading(false);
      }
    }
    loadGraph();
  }, [selectedBorrowerId]);

  return (
    <div className="space-y-8 pb-12">
      {/* Header */}
      <div>
        <h1 className="text-2xl md:text-3xl font-bold text-[#111827] tracking-tight">
          Knowledge Graph
        </h1>
        <p className="text-xs md:text-sm font-medium text-[#6B7280] mt-1">
          Connected credit relationships for{" "}
          <strong className="text-[#111827]">
            {selectedCompany?.company_name || "selected borrower"}
          </strong>.
        </p>
      </div>



      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Graph Canvas (8 Cols) */}
        <div className="lg:col-span-8 bg-white rounded-2xl border border-[#EEF1F5] shadow-[0_4px_20px_rgba(17,24,39,0.04)] p-4 relative h-[520px] overflow-hidden flex items-center justify-center">
          {/* Node Type Legend */}
          <div className="absolute top-4 left-4 z-10 flex gap-2 text-xs flex-wrap">
            {Object.entries(TYPE_COLORS).map(([type, color]) => (
              <div
                key={type}
                className="flex items-center gap-1.5 bg-white px-3 py-1 rounded-full border border-[#EEF1F5] shadow-sm"
                title={TYPE_DESCRIPTIONS[type]}
              >
                <span
                  className="w-2.5 h-2.5 rounded-full shrink-0"
                  style={{ backgroundColor: color }}
                />
                <span className="capitalize font-semibold text-[#6B7280]">
                  {type}
                </span>
              </div>
            ))}
          </div>

          {loading ? (
            <div className="flex items-center gap-2 text-xs font-semibold text-[#6B7280]">
              <Loader2 className="w-5 h-5 animate-spin text-[#7C8DFB]" />
              <span>Loading Knowledge Graph…</span>
            </div>
          ) : nodes.length === 0 ? (
            <div className="text-center text-[#9CA3AF] space-y-3 px-6 max-w-xs">
              <Network className="w-10 h-10 opacity-30 mx-auto" />
              <div>
                <p className="text-sm font-bold text-[#111827]">
                  No graph data yet
                </p>
                <p className="text-xs text-[#6B7280] leading-relaxed mt-1">
                  Upload a credit agreement or SEC filing to generate entity relationships. The graph will populate automatically after document processing.
                </p>
              </div>
            </div>
          ) : (
            <svg className="w-full h-full">
              {edges.map((e, idx) => {
                const source = nodes.find((n) => n.id === e.from);
                const target = nodes.find((n) => n.id === e.to);
                if (!source || !target) return null;

                return (
                  <line
                    key={idx}
                    x1={source.x}
                    y1={source.y}
                    x2={target.x}
                    y2={target.y}
                    stroke="#E5E7EB"
                    strokeWidth="2"
                    strokeDasharray="4 4"
                  />
                );
              })}

              {nodes.map((node) => {
                const isSelected = selectedNode?.id === node.id;
                const color = TYPE_COLORS[node.type] || "#7C8DFB";

                return (
                  <g
                    key={node.id}
                    transform={`translate(${node.x}, ${node.y})`}
                    onClick={() => setSelectedNode(node)}
                    className="cursor-pointer transition-all"
                  >
                    <circle
                      r={isSelected ? 24 : 18}
                      fill={color}
                      opacity={isSelected ? 1 : 0.85}
                      stroke="#ffffff"
                      strokeWidth={isSelected ? 3 : 1}
                    />
                    <text
                      y={34}
                      textAnchor="middle"
                      fill="#111827"
                      fontSize="11"
                      fontWeight="600"
                    >
                      {node.label}
                    </text>
                  </g>
                );
              })}
            </svg>
          )}
        </div>

        {/* Inspector Panel (4 Cols) */}
        <div className="lg:col-span-4 bg-white rounded-2xl border border-[#EEF1F5] shadow-[0_4px_20px_rgba(17,24,39,0.04)] p-6 space-y-4">
          <div className="flex items-center gap-2 font-bold text-sm text-[#111827] pb-3 border-b border-[#EEF1F5]">
            <Info className="w-4 h-4 text-[#7C8DFB]" />
            <span>Node Inspector</span>
          </div>

          {selectedNode ? (
            <div className="space-y-4">
              <div>
                <span className="text-[10px] font-bold uppercase tracking-wider text-[#9CA3AF]">
                  Selected Entity
                </span>
                <h3 className="text-base font-bold text-[#111827] mt-0.5">
                  {selectedNode.label}
                </h3>
                <span
                  className="inline-block mt-1.5 px-2.5 py-0.5 text-xs font-bold rounded-full text-white capitalize"
                  style={{
                    backgroundColor: TYPE_COLORS[selectedNode.type] || "#7C8DFB",
                  }}
                >
                  {selectedNode.type}
                </span>
              </div>

              {/* What this node type means */}
              <div className="p-3 bg-[#E8ECFF] rounded-xl">
                <p className="text-[11px] text-[#4F46E5] font-semibold mb-0.5">
                  What is a {selectedNode.type}?
                </p>
                <p className="text-[11px] text-[#6B7280] leading-relaxed">
                  {TYPE_DESCRIPTIONS[selectedNode.type] || "An entity in the credit knowledge graph."}
                </p>
              </div>

              <div className="pt-1 space-y-2 text-xs">
                <p className="font-semibold text-[#6B7280]">Entity Properties:</p>
                <div className="p-3 bg-[#F8F9FC] border border-[#EEF1F5] rounded-xl text-[#111827] font-mono leading-relaxed break-words text-[11px]">
                  {selectedNode.details}
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center py-8">
              <Network className="w-8 h-8 mx-auto text-[#9CA3AF] opacity-50 mb-2" />
              <p className="text-xs font-semibold text-[#6B7280]">
                Click any node to inspect it.
              </p>
              <p className="text-[11px] text-[#9CA3AF] mt-1 leading-relaxed">
                Each node represents a credit entity. Select one to see its details and relationship context.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
