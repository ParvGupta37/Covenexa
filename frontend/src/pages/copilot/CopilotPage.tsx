import { useState } from "react";
import { BrainCircuit, Send, Sparkles, User, FileText, Loader2, Bot } from "lucide-react";
import api from "@/lib/api";
import { useCompanyStore } from "@/store/company.store";

interface Message {
  id: string;
  sender: "user" | "copilot";
  text: string;
  citations?: string[];
  timestamp: string;
}

const PROMPT_SUGGESTIONS = [
  "Summarize the maintenance covenants.",
  "Which covenant is closest to breach?",
  "What happens if EBITDA drops by 20%?",
  "List all reporting obligations due this quarter.",
];

export default function CopilotPage() {
  const { selectedCompanyId, selectedCompany } = useCompanyStore();
  const selectedBorrowerId = selectedCompanyId;

  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome",
      sender: "copilot",
      text: "Hello! I am Covenexa AI Copilot. Ask me any question regarding borrower credit risk, covenant thresholds, or financial performance.",
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    },
  ]);
  const [inputQuery, setInputQuery] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSend(queryText?: string) {
    const query = queryText || inputQuery;
    if (!query.trim() || loading) return;

    const userMsg: Message = {
      id: Date.now().toString(),
      sender: "user",
      text: query,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputQuery("");
    setLoading(true);

    try {
      const res = await api.post("/api/v1/copilot/query", {
        query: query,
        borrower_id: selectedBorrowerId || undefined,
      });

      const botMsg: Message = {
        id: (Date.now() + 1).toString(),
        sender: "copilot",
        text: res.data.response,
        citations: res.data.citations,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };

      setMessages((prev) => [...prev, botMsg]);
    } catch (e) {
      console.error("Copilot error", e);
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          sender: "copilot",
          text: "I encountered an error querying the intelligence engine. Please try again.",
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="h-[calc(100vh-8rem)] flex flex-col justify-between space-y-4">
      {/* Top Header */}
      <div className="flex items-center justify-between pb-3 border-b border-border">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-primary/20 text-primary rounded-xl border border-primary/30">
            <BrainCircuit className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-foreground">Covenexa AI Credit Copilot</h1>
            <p className="text-xs text-muted-foreground">Hybrid GraphRAG Q&A engine powered by Cohere Command A</p>
          </div>
        </div>

        {selectedCompany && (
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-card border border-border text-xs font-semibold">
            <Sparkles className="w-3.5 h-3.5 text-primary" /> Context: <span className="text-primary">{selectedCompany.company_name}</span>
          </div>
        )}
      </div>

      {/* Message Chat Feed */}
      <div className="flex-1 overflow-y-auto space-y-4 pr-2">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex gap-3 text-sm ${msg.sender === "user" ? "justify-end" : "justify-start"}`}
          >
            {msg.sender === "copilot" && (
              <div className="w-8 h-8 rounded-full bg-primary/20 text-primary flex items-center justify-center border border-primary/30 shrink-0 mt-1">
                <Bot className="w-4 h-4" />
              </div>
            )}

            <div className={`max-w-2xl rounded-2xl p-4 shadow-sm space-y-2 ${
              msg.sender === "user"
                ? "bg-primary text-primary-foreground font-medium rounded-tr-none"
                : "bg-card border border-border text-foreground rounded-tl-none"
            }`}>
              <p className="leading-relaxed whitespace-pre-wrap">{msg.text}</p>

              {msg.citations && msg.citations.length > 0 && (
                <div className="pt-2 border-t border-border/40 text-xs space-y-1 text-muted-foreground">
                  <span className="font-semibold flex items-center gap-1"><FileText className="w-3 h-3" /> Cited Sources:</span>
                  {msg.citations.map((c, i) => (
                    <p key={i} className="truncate">• {c}</p>
                  ))}
                </div>
              )}

              <span className="block text-[10px] opacity-60 text-right">{msg.timestamp}</span>
            </div>

            {msg.sender === "user" && (
              <div className="w-8 h-8 rounded-full bg-muted text-muted-foreground flex items-center justify-center border border-border shrink-0 mt-1">
                <User className="w-4 h-4" />
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Prompt Suggestions */}
      <div className="flex gap-2 flex-wrap text-xs">
        {PROMPT_SUGGESTIONS.map((s, idx) => (
          <button
            key={idx}
            onClick={() => handleSend(s)}
            className="px-3 py-1.5 bg-card border border-border rounded-full hover:border-primary/50 text-muted-foreground hover:text-foreground transition-all"
          >
            {s}
          </button>
        ))}
      </div>

      {/* Input Box */}
      <div className="flex gap-2 bg-card border border-border p-2 rounded-2xl shadow-md">
        <input
          type="text"
          value={inputQuery}
          onChange={(e) => setInputQuery(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSend()}
          placeholder={`Ask AI Copilot about ${selectedCompany?.company_name || "portfolio entities"}...`}
          className="flex-1 bg-transparent px-4 py-2 text-sm focus:outline-none text-foreground placeholder:text-muted-foreground/60"
        />
        <button
          onClick={() => handleSend()}
          disabled={loading || !inputQuery.trim()}
          className="px-5 py-2.5 bg-primary text-primary-foreground font-semibold rounded-xl text-sm hover:bg-primary/90 transition-all disabled:opacity-50 flex items-center gap-2"
        >
          {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />} Ask Copilot
        </button>
      </div>
    </div>
  );
}
