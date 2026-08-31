import { useEffect, useState, useRef, useMemo } from "react";
import {
  BrainCircuit,
  Send,
  Loader2,
  Bot,
  Building2,
  Database,
  Search,
  Network,
  FileText,
  Lightbulb,
  PlusCircle,
  MessageSquare,
  Trash2,
  Clock,
  Info,
  ChevronDown,
} from "lucide-react";
import api from "@/lib/api";
import { useCompanyStore } from "@/store/company.store";
import { MarkdownRenderer } from "@/components/copilot/MarkdownRenderer";
import { CitationCard } from "@/components/copilot/CitationCard";
import { normalizeCitations } from "@/utils/normalizeEvidence";

interface Message {
  id: string;
  sender: "user" | "copilot";
  text: string;
  citations?: string[];
  hybrid_status?: { sql?: boolean; graph?: boolean; vector?: boolean };
  timestamp: string;
}

interface ConversationSummary {
  id: string;
  organization_id: string;
  user_id?: string;
  borrower_id?: string;
  title: string;
  message_count: number;
  created_at: string;
  updated_at: string;
}

function cleanAnswerText(text: string): string {
  if (!text) return "";
  return text
    .replace(/\[(?:PostgreSQL|Neo4j|Pinecone|SQL|Graph|Vector)\]/gi, "")
    .replace(/\[SOURCE:\s*[^\]]+\]/gi, "")
    .replace(/\[LIMITATION NOTICE:[^\]]+\]/gi, "")
    .replace(/\(\s*\)/g, "")
    .replace(/[ \t]+/g, " ")
    .trim();
}

const PROMPT_SUGGESTIONS = [
  { text: "Why is this borrower high risk?", category: "Risk" },
  { text: "What covenants are most at risk?", category: "Covenants" },
  { text: "What does the agreement say about leverage?", category: "Agreement" },
  { text: "What changed in this borrower's risk profile?", category: "Trends" },
  { text: "Summarize the key financial metrics.", category: "Financials" },
];

export default function CopilotPage() {
  const { selectedCompanyId, selectedCompany } = useCompanyStore();
  const selectedBorrowerId = selectedCompanyId;

  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputQuery, setInputQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [latestCitations, setLatestCitations] = useState<string[]>([]);
  const [showSuggestionsDropdown, setShowSuggestionsDropdown] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const suggestionsDropdownRef = useRef<HTMLDivElement>(null);

  const [activeCategoryFilter, setActiveCategoryFilter] = useState<
    "all" | "financial" | "document" | "knowledge_graph"
  >("all");

  const { evidences: normalizedEvidenceList, limitationNotice, counts } = useMemo(
    () => normalizeCitations(latestCitations),
    [latestCitations]
  );

  const filteredEvidenceList = useMemo(() => {
    if (activeCategoryFilter === "all") return normalizedEvidenceList;
    return normalizedEvidenceList.filter((e) => e.type === activeCategoryFilter);
  }, [normalizedEvidenceList, activeCategoryFilter]);

  const welcomeMessage: Message = {
    id: "welcome",
    sender: "copilot",
    text: `Ask questions about borrowers, agreements, financial risk, or covenants. Covenexa retrieves relevant evidence from financial data, extracted documents, and the knowledge graph before generating an answer.${
      selectedCompany ? `\n\nCurrently focused on: **${selectedCompany.company_name}**.` : ""
    }`,
    timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
  };

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (
        suggestionsDropdownRef.current &&
        !suggestionsDropdownRef.current.contains(event.target as Node)
      ) {
        setShowSuggestionsDropdown(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Fetch conversations scoped to user / borrower
  useEffect(() => {
    async function fetchConversations() {
      try {
        setLoadingHistory(true);
        const res = await api.get("/api/v1/copilot/conversations", {
          params: { borrower_id: selectedBorrowerId || undefined },
        });
        setConversations(res.data || []);
      } catch (err) {
        console.error("Failed to load Copilot conversations", err);
      } finally {
        setLoadingHistory(false);
      }
    }
    fetchConversations();
  }, [selectedBorrowerId]);

  // Reset to clean New Chat whenever active borrower changes
  useEffect(() => {
    setActiveConversationId(null);
    setMessages([
      {
        id: "welcome-" + (selectedBorrowerId || "none"),
        sender: "copilot",
        text: `Ask questions about borrowers, agreements, financial risk, or covenants. Covenexa retrieves relevant evidence from financial data, extracted documents, and the knowledge graph before generating an answer.${
          selectedCompany ? `\n\nCurrently focused on: **${selectedCompany.company_name}**.` : ""
        }`,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      },
    ]);
    setLatestCitations([]);
  }, [selectedBorrowerId, selectedCompany]);

  async function loadConversationDetails(convId: string) {
    try {
      const res = await api.get(`/api/v1/copilot/conversations/${convId}`);
      const data = res.data;
      if (data && data.messages && data.messages.length > 0) {
        const mapped: Message[] = data.messages.map((m: any) => ({
          id: m.id,
          sender: m.role === "user" ? "user" : "copilot",
          text: m.role === "user" ? m.content : cleanAnswerText(m.content),
          citations: m.citations || [],
          hybrid_status: m.hybrid_retrieval_status,
          timestamp: new Date(m.created_at).toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
          }),
        }));
        setMessages(mapped);

        // Find latest assistant message with citations
        for (let i = mapped.length - 1; i >= 0; i--) {
          if (mapped[i].sender === "copilot" && mapped[i].citations && mapped[i].citations!.length > 0) {
            setLatestCitations(mapped[i].citations!);
            break;
          }
        }
      } else {
        setMessages([welcomeMessage]);
        setLatestCitations([]);
      }
    } catch (e) {
      console.error("Failed to load conversation messages", e);
    }
  }

  async function handleSelectConversation(convId: string) {
    if (convId === activeConversationId) return;
    setActiveConversationId(convId);
    setLoadingHistory(true);
    await loadConversationDetails(convId);
    setLoadingHistory(false);
  }

  function handleNewChat() {
    setActiveConversationId(null);
    setMessages([welcomeMessage]);
    setLatestCitations([]);
  }

  async function handleDeleteConversation(e: React.MouseEvent, convId: string) {
    e.stopPropagation();
    try {
      await api.delete(`/api/v1/copilot/conversations/${convId}`);
      setConversations((prev) => prev.filter((c) => c.id !== convId));
      if (activeConversationId === convId) {
        handleNewChat();
      }
    } catch (err) {
      console.error("Failed to delete conversation", err);
    }
  }

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
        conversation_id: activeConversationId || undefined,
      });

      const responseText =
        (typeof res.data?.response === "string" && res.data.response.trim()) ||
        (typeof res.data?.answer === "string" && res.data.answer.trim()) ||
        (typeof res.data?.text === "string" && res.data.text.trim()) ||
        "No response generated from the intelligence engine. Please try again.";

      const cleanedText = cleanAnswerText(responseText);

      const newConvId = res.data?.conversation_id;
      if (newConvId && newConvId !== activeConversationId) {
        setActiveConversationId(newConvId);
        // Refresh conversation list in background
        api
          .get("/api/v1/copilot/conversations", {
            params: { borrower_id: selectedBorrowerId || undefined },
          })
          .then((r) => setConversations(r.data || []))
          .catch(() => {});
      }

      const botMsg: Message = {
        id: res.data?.message_id || (Date.now() + 1).toString(),
        sender: "copilot",
        text: cleanedText,
        citations: res.data.citations,
        hybrid_status: res.data.hybrid_retrieval_status,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };

      setMessages((prev) => [...prev, botMsg]);
      if (res.data.citations && res.data.citations.length > 0) {
        setLatestCitations(res.data.citations);
      }
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
    <div className="h-[calc(100vh-6.5rem)] flex flex-col space-y-4 pb-2">
      {/* Top Header */}
      <div className="flex items-center justify-between pb-3 border-b border-[#EEF1F5] shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl bg-[#E8ECFF] text-[#4F46E5] flex items-center justify-center shrink-0 shadow-xs">
            <BrainCircuit className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-[#111827]">AI Credit Copilot</h1>
            <p className="text-xs font-medium text-[#6B7280]">
              Evidence-backed answers from financial data, documents, and knowledge graph
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {selectedCompany && (
            <div className="flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-white border border-[#EEF1F5] text-xs font-semibold text-[#111827] shadow-xs">
              <Building2 className="w-3.5 h-3.5 text-[#7C8DFB]" />
              <span className="text-[#6B7280]">Context:</span>
              <span className="font-bold text-[#4F46E5]">{selectedCompany.company_name}</span>
            </div>
          )}

          <button
            onClick={handleNewChat}
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-[#E8ECFF] text-[#4F46E5] hover:bg-[#7C8DFB] hover:text-white transition-all text-xs font-semibold shadow-xs"
          >
            <PlusCircle className="w-3.5 h-3.5" />
            <span>New Chat</span>
          </button>
        </div>
      </div>

      {/* 2-Column 60-40 Main Layout */}
      <div className="flex flex-col lg:flex-row gap-5 flex-1 min-h-0">
        {/* Left Side: Chatbot Feed & Input (60% Width) */}
        <div className="w-full lg:w-[60%] flex flex-col justify-between bg-white rounded-2xl border border-[#EEF1F5] shadow-[0_4px_20px_rgba(17,24,39,0.04)] p-5 min-h-0">
          {/* Messages Feed */}
          <div className="flex-1 overflow-y-auto space-y-4 pr-2 min-h-0">
            {loadingHistory ? (
              <div className="h-full flex items-center justify-center text-xs text-[#9CA3AF] gap-2">
                <Loader2 className="w-4 h-4 animate-spin text-[#7C8DFB]" />
                <span>Restoring conversation history…</span>
              </div>
            ) : (
              messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`flex gap-3 text-xs ${
                    msg.sender === "user" ? "justify-end" : "justify-start"
                  }`}
                >
                  {msg.sender === "copilot" && (
                    <div className="w-8 h-8 rounded-full bg-[#E8ECFF] text-[#4F46E5] flex items-center justify-center shrink-0 mt-0.5 shadow-2xs">
                      <Bot className="w-4 h-4" />
                    </div>
                  )}

                  <div
                    className={`max-w-xl md:max-w-2xl rounded-2xl p-4 space-y-2 ${
                      msg.sender === "user"
                        ? "bg-[#7C8DFB] text-white font-medium rounded-tr-none shadow-sm"
                        : "bg-[#F8F9FC] border border-[#EEF1F5] text-[#111827] rounded-tl-none shadow-2xs"
                    }`}
                  >
                    {msg.sender === "copilot" && msg.citations && msg.citations.length > 0 && (
                      <div className="flex items-center gap-1 mb-1.5 pb-1 border-b border-[#EEF1F5]/60">
                        <span className="text-[9px] font-bold uppercase tracking-wider text-[#7C8DFB] bg-[#E8ECFF] px-2 py-0.5 rounded-full">
                          AI Analysis
                        </span>
                        <span className="text-[9px] text-[#9CA3AF]">
                          · {msg.citations.length} source{msg.citations.length !== 1 ? "s" : ""} retrieved
                        </span>
                      </div>
                    )}
                    {msg.sender === "user" ? (
                      <p className="leading-relaxed whitespace-pre-wrap text-xs md:text-sm">
                        {msg.text || ""}
                      </p>
                    ) : (
                      <MarkdownRenderer content={msg.text || "Unable to display response."} />
                    )}

                    <span className="block text-[10px] opacity-60 text-right pt-1">
                      {msg.timestamp}
                    </span>
                  </div>

                  {msg.sender === "user" && (
                    <div className="w-8 h-8 rounded-full bg-[#111827] text-white flex items-center justify-center shrink-0 mt-0.5 text-xs font-bold shadow-2xs">
                      U
                    </div>
                  )}
                </div>
              ))
            )}

            {loading && (
              <div className="flex gap-3 justify-start">
                <div className="w-8 h-8 rounded-full bg-[#E8ECFF] text-[#4F46E5] flex items-center justify-center shrink-0 shadow-2xs">
                  <Bot className="w-4 h-4" />
                </div>
                <div className="bg-[#F8F9FC] border border-[#EEF1F5] rounded-2xl rounded-tl-none px-5 py-4 flex items-center gap-2">
                  <Loader2 className="w-3.5 h-3.5 animate-spin text-[#7C8DFB]" />
                  <span className="text-xs text-[#6B7280]">Retrieving evidence…</span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Bottom Area: Compact Suggested Questions Dropdown & Input Box */}
          <div className="mt-3 space-y-2 pt-2 border-t border-[#EEF1F5]">
            <div className="flex items-center justify-between">
              {/* Suggested Questions Dropdown (Space Saver) */}
              <div className="relative" ref={suggestionsDropdownRef}>
                <button
                  type="button"
                  onClick={() => setShowSuggestionsDropdown(!showSuggestionsDropdown)}
                  className="flex items-center gap-1.5 px-3 py-1.5 bg-[#F8F9FC] hover:bg-[#E8ECFF] border border-[#EEF1F5] rounded-xl text-xs font-medium text-[#4B5563] hover:text-[#4F46E5] transition-all shadow-2xs"
                >
                  <Lightbulb className="w-3.5 h-3.5 text-[#7C8DFB]" />
                  <span>Suggested Questions</span>
                  <ChevronDown
                    className={`w-3 h-3 text-[#9CA3AF] transition-transform ${
                      showSuggestionsDropdown ? "rotate-180" : ""
                    }`}
                  />
                </button>

                {showSuggestionsDropdown && (
                  <div className="absolute bottom-full left-0 mb-2 w-80 md:w-96 bg-white border border-[#EEF1F5] rounded-2xl shadow-xl p-2 z-50 space-y-1">
                    <p className="text-[10px] font-bold text-[#9CA3AF] uppercase tracking-wider px-2 py-1">
                      Select a Suggested Question
                    </p>
                    {PROMPT_SUGGESTIONS.map((s, idx) => (
                      <button
                        key={idx}
                        onClick={() => {
                          setShowSuggestionsDropdown(false);
                          handleSend(s.text);
                        }}
                        className="w-full text-left px-2.5 py-1.5 rounded-lg text-xs hover:bg-[#F4F6FD] text-[#374151] hover:text-[#111827] flex items-center justify-between group transition-colors"
                      >
                        <span className="truncate pr-2 font-medium">{s.text}</span>
                        <span className="text-[9px] font-semibold uppercase text-[#7C8DFB] bg-[#E8ECFF] px-1.5 py-0.5 rounded shrink-0">
                          {s.category}
                        </span>
                      </button>
                    ))}
                  </div>
                )}
              </div>

              <span className="text-[10px] text-[#9CA3AF] font-medium hidden sm:inline">
                Press Enter to send
              </span>
            </div>

            {/* Input Bar */}
            <div className="flex gap-2 bg-[#F8F9FC] border border-[#EEF1F5] p-1.5 rounded-2xl">
              <input
                type="text"
                value={inputQuery}
                onChange={(e) => setInputQuery(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSend()}
                placeholder={`Ask about ${
                  selectedCompany?.company_name || "borrower credit, covenants, or agreements"
                }…`}
                className="flex-1 bg-transparent px-3.5 py-2 text-xs font-medium focus:outline-none text-[#111827] placeholder:text-[#9CA3AF]"
              />
              <button
                onClick={() => handleSend()}
                disabled={loading || !inputQuery.trim()}
                className="px-5 py-2 bg-[#7C8DFB] text-white font-semibold rounded-xl text-xs hover:bg-[#6366F1] transition-all disabled:opacity-50 flex items-center gap-2 shadow-sm shrink-0"
              >
                {loading ? (
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <Send className="w-3.5 h-3.5" />
                )}
                <span>Ask</span>
              </button>
            </div>
          </div>
        </div>

        {/* Right Side: Recent Chats (First) & Evidence (Second) (40% Width) */}
        <div className="w-full lg:w-[40%] flex flex-col gap-4 min-h-0 overflow-y-auto pr-1">
          {/* 1. Recent Chats Card (First) */}
          <div className="bg-white rounded-2xl border border-[#EEF1F5] shadow-[0_4px_20px_rgba(17,24,39,0.04)] p-4 flex flex-col shrink-0 max-h-56">
            <div className="flex items-center justify-between mb-2.5 pb-2 border-b border-[#EEF1F5]">
              <div className="flex items-center gap-1.5 text-xs font-bold text-[#111827]">
                <MessageSquare className="w-3.5 h-3.5 text-[#7C8DFB]" />
                <span>Recent Chats</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-[10px] text-[#9CA3AF] font-medium font-mono">
                  {conversations.length}
                </span>
                <button
                  onClick={handleNewChat}
                  title="Create New Chat"
                  className="p-1 text-[#4F46E5] hover:bg-[#E8ECFF] rounded-lg transition-all"
                >
                  <PlusCircle className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>

            <div className="flex-1 overflow-y-auto space-y-1.5 pr-1 min-h-0">
              {loadingHistory && conversations.length === 0 ? (
                <div className="py-6 text-center text-xs text-[#9CA3AF] flex items-center justify-center gap-2">
                  <Loader2 className="w-3.5 h-3.5 animate-spin text-[#7C8DFB]" />
                  <span>Loading chats…</span>
                </div>
              ) : conversations.length === 0 ? (
                <div className="text-center py-6 text-[#9CA3AF]">
                  <Clock className="w-5 h-5 mx-auto mb-1 opacity-40" />
                  <p className="text-xs font-medium text-[#6B7280]">No previous chats</p>
                  <p className="text-[10px] text-[#9CA3AF] mt-0.5">Start asking questions</p>
                </div>
              ) : (
                conversations.map((c) => {
                  const isActive = c.id === activeConversationId;
                  return (
                    <div
                      key={c.id}
                      onClick={() => handleSelectConversation(c.id)}
                      className={`group relative p-2.5 rounded-xl border text-xs cursor-pointer transition-all ${
                        isActive
                          ? "bg-[#F4F6FD] border-[#7C8DFB] text-[#111827] shadow-xs font-semibold"
                          : "bg-[#F8F9FC] border-transparent hover:border-[#EEF1F5] text-[#4B5563] hover:text-[#111827]"
                      }`}
                    >
                      <div className="flex items-start justify-between gap-1.5">
                        <p className="line-clamp-2 leading-snug flex-1">{c.title}</p>
                        <button
                          onClick={(e) => handleDeleteConversation(e, c.id)}
                          title="Delete conversation"
                          className="opacity-0 group-hover:opacity-100 text-[#9CA3AF] hover:text-red-500 transition-opacity p-0.5 shrink-0"
                        >
                          <Trash2 className="w-3 h-3" />
                        </button>
                      </div>
                      <div className="flex items-center justify-between mt-1 text-[9px] text-[#9CA3AF] font-normal">
                        <span>{c.message_count} msgs</span>
                        <span>
                          {new Date(c.updated_at).toLocaleDateString([], {
                            month: "short",
                            day: "numeric",
                          })}
                        </span>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </div>

          {/* 2. Evidence Card (Second / Below Recent Chats) */}
          <div className="bg-white rounded-2xl border border-[#EEF1F5] shadow-[0_4px_20px_rgba(17,24,39,0.04)] p-4 flex flex-col flex-1 min-h-0 overflow-y-auto">
            <div className="pb-2 mb-2.5 border-b border-[#EEF1F5]">
              <h3 className="text-sm font-bold text-[#111827]">Evidence</h3>
              <p className="text-[11px] text-[#6B7280] leading-tight mt-0.5">
                Multi-source retrieved evidence grounding the AI response.
              </p>
            </div>

            {/* Interactive Category Filter Tabs */}
            <div className="flex items-center gap-1 mb-3 p-1 bg-[#F8F9FC] border border-[#EEF1F5] rounded-xl text-[10px]">
              <button
                type="button"
                onClick={() => setActiveCategoryFilter("all")}
                className={`flex-1 flex items-center justify-center gap-1 py-1.5 px-1 rounded-lg font-medium transition-all ${
                  activeCategoryFilter === "all"
                    ? "bg-white text-[#111827] shadow-xs font-bold border border-[#EEF1F5]"
                    : "text-[#6B7280] hover:text-[#111827]"
                }`}
              >
                <span>All</span>
                <span className="text-[9px] px-1 py-0.2 rounded-full bg-[#EEF1F5] font-mono">
                  {counts?.total || 0}
                </span>
              </button>

              <button
                type="button"
                onClick={() =>
                  setActiveCategoryFilter(activeCategoryFilter === "financial" ? "all" : "financial")
                }
                className={`flex-1 flex items-center justify-center gap-1 py-1.5 px-1 rounded-lg font-medium transition-all ${
                  activeCategoryFilter === "financial"
                    ? "bg-emerald-50 text-emerald-700 font-bold border border-emerald-200 shadow-xs"
                    : "text-[#6B7280] hover:text-emerald-700"
                }`}
              >
                <Database className="w-3 h-3 text-[#10B981] shrink-0" />
                <span className="truncate">Financial</span>
                <span className="text-[9px] px-1 py-0.2 rounded-full bg-[#EEF1F5] font-mono">
                  {counts?.financial || 0}
                </span>
              </button>

              <button
                type="button"
                onClick={() =>
                  setActiveCategoryFilter(activeCategoryFilter === "document" ? "all" : "document")
                }
                className={`flex-1 flex items-center justify-center gap-1 py-1.5 px-1 rounded-lg font-medium transition-all ${
                  activeCategoryFilter === "document"
                    ? "bg-indigo-50 text-indigo-700 font-bold border border-indigo-200 shadow-xs"
                    : "text-[#6B7280] hover:text-indigo-700"
                }`}
              >
                <Search className="w-3 h-3 text-[#7C8DFB] shrink-0" />
                <span className="truncate">Document</span>
                <span className="text-[9px] px-1 py-0.2 rounded-full bg-[#EEF1F5] font-mono">
                  {counts?.document || 0}
                </span>
              </button>

              <button
                type="button"
                onClick={() =>
                  setActiveCategoryFilter(
                    activeCategoryFilter === "knowledge_graph" ? "all" : "knowledge_graph"
                  )
                }
                className={`flex-1 flex items-center justify-center gap-1 py-1.5 px-1 rounded-lg font-medium transition-all ${
                  activeCategoryFilter === "knowledge_graph"
                    ? "bg-amber-50 text-amber-700 font-bold border border-amber-200 shadow-xs"
                    : "text-[#6B7280] hover:text-amber-700"
                }`}
              >
                <Network className="w-3 h-3 text-[#F97316] shrink-0" />
                <span className="truncate">Graph</span>
                <span className="text-[9px] px-1 py-0.2 rounded-full bg-[#EEF1F5] font-mono">
                  {counts?.knowledge_graph || 0}
                </span>
              </button>
            </div>

            {normalizedEvidenceList.length > 0 ? (
              <div className="space-y-2.5">
                <div className="flex items-center justify-between">
                  <p className="text-[10px] font-bold text-[#9CA3AF] uppercase tracking-wide">
                    {filteredEvidenceList.length} of {normalizedEvidenceList.length} citation
                    {normalizedEvidenceList.length !== 1 ? "s" : ""} shown
                  </p>
                  {activeCategoryFilter !== "all" && (
                    <button
                      type="button"
                      onClick={() => setActiveCategoryFilter("all")}
                      className="text-[10px] font-semibold text-[#4F46E5] hover:underline"
                    >
                      Clear filter
                    </button>
                  )}
                </div>

                {filteredEvidenceList.length > 0 ? (
                  filteredEvidenceList.map((evidence, idx) => (
                    <CitationCard key={evidence.id || idx} evidence={evidence} index={idx} />
                  ))
                ) : (
                  <div className="text-center py-6 p-4 bg-[#F8F9FC] rounded-xl border border-[#EEF1F5] text-[#9CA3AF]">
                    <p className="text-xs font-semibold text-[#6B7280]">
                      No {activeCategoryFilter === "financial"
                        ? "Financial"
                        : activeCategoryFilter === "document"
                        ? "Document"
                        : "Knowledge Graph"}{" "}
                      citations found
                    </p>
                    <button
                      type="button"
                      onClick={() => setActiveCategoryFilter("all")}
                      className="mt-2 text-[11px] font-medium text-[#4F46E5] hover:underline block mx-auto"
                    >
                      Show all citations ({counts?.total || 0})
                    </button>
                  </div>
                )}

                {limitationNotice && (
                  <div className="mt-2.5 p-2.5 bg-[#F8F9FC] border border-[#EEF1F5] rounded-xl text-[11px] text-[#6B7280] flex items-start gap-2">
                    <Info className="w-3.5 h-3.5 text-[#7C8DFB] shrink-0 mt-0.5" />
                    <span className="leading-snug">{limitationNotice}</span>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-6 text-[#9CA3AF]">
                <FileText className="w-6 h-6 mx-auto mb-1.5 opacity-40" />
                <p className="text-xs font-semibold text-[#6B7280]">No citations yet.</p>
                <p className="text-[11px] mt-0.5 leading-relaxed">
                  Ask a question to see what evidence Covenexa retrieved.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
