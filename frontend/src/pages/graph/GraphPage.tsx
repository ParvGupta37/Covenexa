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
  borrower: "#10b981",
  loan: "#3b82f6",
  agreement: "#8b5cf6",
  covenant: "#f59e0b",
  financial: "#ec4899",
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
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Credit Knowledge Graph</h1>
          <p className="text-muted-foreground mt-1">Live relationship graph connecting Borrowers, Facilities, Agreements, Covenants, and Financials</p>
        </div>

        {selectedCompany && (
          <span className="text-sm font-semibold text-foreground bg-card border border-border px-4 py-2 rounded-lg">
            Topology Entity: <span className="text-primary">{selectedCompany.company_name}</span>
          </span>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* SVG Graph Canvas */}
        <div className="lg:col-span-3 bg-card border border-border rounded-2xl p-4 shadow-sm relative h-[520px] overflow-hidden flex items-center justify-center">
          <div className="absolute top-4 left-4 z-10 flex gap-3 text-xs flex-wrap">
            {Object.entries(TYPE_COLORS).map(([type, color]) => (
              <div key={type} className="flex items-center gap-1.5 bg-background/80 px-2.5 py-1 rounded-full border border-border shadow-sm">
                <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: color }} />
                <span className="capitalize text-muted-foreground font-semibold">{type}</span>
              </div>
            ))}
          </div>

          {loading ? (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Loader2 className="w-5 h-5 animate-spin text-primary" /> Querying Graph Topology...
            </div>
          ) : nodes.length === 0 ? (
            <div className="text-center text-muted-foreground text-sm space-y-1">
              <Network className="w-10 h-10 opacity-30 mx-auto mb-2" />
              <p className="font-semibold">No graph nodes for this company yet</p>
              <p className="text-xs">Upload an agreement or SEC filing to generate entity connections.</p>
            </div>
          ) : (
            <svg className="w-full h-full">
              {/* Draw Edges */}
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
                    stroke="#374151"
                    strokeWidth="2"
                    strokeDasharray="4 4"
                  />
                );
              })}

              {/* Draw Nodes */}
              {nodes.map((node) => {
                const isSelected = selectedNode?.id === node.id;
                const color = TYPE_COLORS[node.type] || "#3b82f6";

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
                      className="hover:scale-110 transition-all"
                    />
                    <text
                      y={34}
                      textAnchor="middle"
                      fill="#e5e7eb"
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

        {/* Node Inspector Panel */}
        <div className="bg-card border border-border p-6 rounded-2xl shadow-sm space-y-4">
          <div className="flex items-center gap-2 font-bold border-b border-border pb-3 text-foreground">
            <Info className="w-4 h-4 text-primary" /> Node Inspector
          </div>

          {selectedNode ? (
            <div className="space-y-3">
              <div>
                <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Selected Entity Node</span>
                <h3 className="text-lg font-bold text-foreground mt-0.5">{selectedNode.label}</h3>
                <span
                  className="inline-block mt-1 px-2.5 py-0.5 text-xs font-bold rounded-full uppercase text-white"
                  style={{ backgroundColor: TYPE_COLORS[selectedNode.type] || "#3b82f6" }}
                >
                  {selectedNode.type}
                </span>
              </div>

              <div className="pt-3 border-t border-border space-y-2 text-xs">
                <p className="font-semibold text-muted-foreground">Properties & Data:</p>
                <div className="p-3 bg-muted/40 rounded-xl text-foreground font-mono leading-relaxed break-words">
                  {selectedNode.details}
                </div>
              </div>
            </div>
          ) : (
            <p className="text-xs text-muted-foreground">Click any graph node to inspect live entity metadata.</p>
          )}
        </div>
      </div>
    </div>
  );
}
