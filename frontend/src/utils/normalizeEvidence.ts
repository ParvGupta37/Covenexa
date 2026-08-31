/**
 * Evidence & Citation Normalization Utility for AI Credit Copilot.
 * Transforms raw backend debug strings into clean, user-facing structured evidence.
 */

export interface NormalizedEvidence {
  id: string;
  type: "financial" | "document" | "knowledge_graph" | "generic";
  label: "Financial Data" | "Document Extract" | "Knowledge Graph" | "Evidence";
  available: boolean;
  title?: string;
  documentName?: string;
  page?: number;
  pages?: (number | string)[];
  section?: string;
  items: string[];
  excerpt?: string;
}

export interface EvidenceNormalizationResult {
  evidences: NormalizedEvidence[];
  limitationNotice?: string;
  counts: {
    financial: number;
    document: number;
    knowledge_graph: number;
    total: number;
  };
}

/**
 * Strips raw UUIDs, Chunk IDs, and internal tags from text.
 */
function cleanText(raw: string): string {
  if (!raw) return "";
  return raw
    .replace(/\[(?:PostgreSQL|Neo4j|Pinecone|SQL|Graph|Vector)\]/gi, "")
    .replace(/###\s*\[SOURCE:[^\]]+\]/gi, "")
    .replace(/\[SOURCE:[^\]]+\]/gi, "")
    .replace(/Document Chunk ID:\s*[a-f0-9-]+/gi, "")
    .replace(/[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}/gi, "")
    .replace(/Section\s*['"]none['"]/gi, "")
    .replace(/Section\s*['"]null['"]/gi, "")
    .replace(/\[Document Passage\s*[^\]]*\]:?/gi, "")
    .replace(/\s+/g, " ")
    .trim();
}

/**
 * Normalizes an array of raw backend citation strings into structured evidence objects.
 */
export function normalizeCitations(rawCitations: string[]): EvidenceNormalizationResult {
  if (!rawCitations || !Array.isArray(rawCitations) || rawCitations.length === 0) {
    return {
      evidences: [],
      counts: { financial: 0, document: 0, knowledge_graph: 0, total: 0 },
    };
  }

  const evidences: NormalizedEvidence[] = [];
  let limitationNotice: string | undefined = undefined;

  // Track document pages when no full excerpts are available
  const referredPages: Set<number | string> = new Set();
  const documentPassagesWithText: NormalizedEvidence[] = [];

  rawCitations.forEach((raw, idx) => {
    if (!raw || typeof raw !== "string") return;
    const trimmed = raw.trim();
    if (!trimmed) return;

    // 1. Check for Limitation Notice
    if (
      trimmed.includes("[LIMITATION NOTICE:") ||
      trimmed.startsWith("LIMITATION NOTICE:") ||
      trimmed.includes("LIMITATION NOTICE")
    ) {
      if (trimmed.includes("Neo4j") || trimmed.includes("Knowledge Graph")) {
        limitationNotice =
          "Knowledge Graph was unavailable for this query. Responses were synthesized using available financial and document evidence.";
      } else if (trimmed.includes("Pinecone") || trimmed.includes("Vector")) {
        limitationNotice =
          "Document passage search was unavailable for this query. Responses were synthesized using structured financial data and knowledge graph.";
      } else if (trimmed.includes("SQL-Only")) {
        limitationNotice =
          "Document search and Knowledge Graph were unavailable for this query. Responses were synthesized using verified structured financial records.";
      } else {
        limitationNotice =
          "Operating with partial data sources. Verified financial records were prioritized for this analysis.";
      }
      return;
    }

    // 2. Identify Source Type
    const isSQL =
      trimmed.includes("PostgreSQL") ||
      trimmed.includes("SQL Structured Data") ||
      trimmed.includes("Borrower:") ||
      trimmed.includes("Financial Metrics");

    const isVector =
      trimmed.includes("Pinecone") ||
      trimmed.includes("Vector Search") ||
      trimmed.includes("Document Passage") ||
      trimmed.includes("Referred Document");

    const isGraph =
      trimmed.includes("Neo4j") ||
      trimmed.includes("Knowledge Graph") ||
      trimmed.includes("->");

    // 3. Check for "Unavailable" Status
    const isUnavailable =
      trimmed.includes("Status: Knowledge Graph traversal unavailable") ||
      trimmed.includes("Status: Vector document passage retrieval unavailable") ||
      trimmed.includes("Status: No structured borrower metrics") ||
      trimmed.includes("traversal unavailable or no linked graph") ||
      trimmed.includes("retrieval unavailable or no matching agreement");

    if (isSQL) {
      if (isUnavailable) {
        evidences.push({
          id: `financial-${idx}`,
          type: "financial",
          label: "Financial Data",
          available: false,
          items: ["No structured financial metrics or covenant records available for this entity."],
        });
        return;
      }

      // Parse structured lines
      const cleanLines = trimmed
        .replace(/^###\s*\[SOURCE:[^\]]+\]/im, "")
        .split("\n")
        .map((line) => line.replace(/^[-*•]\s*/, "").trim())
        .filter((line) => line && !line.startsWith("Status:"));

      const items: string[] = [];
      cleanLines.forEach((line) => {
        if (line.includes(" | ")) {
          const parts = line.split(" | ").map((p) => cleanText(p)).filter(Boolean);
          items.push(...parts);
        } else {
          const cleaned = cleanText(line);
          if (cleaned) items.push(cleaned);
        }
      });

      if (items.length > 0) {
        evidences.push({
          id: `financial-${idx}`,
          type: "financial",
          label: "Financial Data",
          available: true,
          title: "Borrower Financial & Risk Metrics",
          items,
        });
      }
      return;
    }

    if (isVector) {
      if (isUnavailable) {
        evidences.push({
          id: `document-${idx}`,
          type: "document",
          label: "Document Extract",
          available: false,
          items: ["No matching document passages retrieved for this query."],
        });
        return;
      }

      // Extract document passage content
      const passageBlocks = trimmed
        .replace(/^###\s*\[SOURCE:[^\]]+\]/im, "")
        .split("\n")
        .map((l) => l.replace(/^[-*•]\s*/, "").trim())
        .filter((l) => l && !l.startsWith("Status:"));

      passageBlocks.forEach((block, bIdx) => {
        let pageNum: number | undefined = undefined;
        let sectionName: string | undefined = undefined;
        let mainContent = block;

        // Parse header: [Document Passage | Page 1, Section 'none': ...]
        const match = block.match(
          /\[Document Passage\s*(?:\|\s*(?:File:\s*([^|]+)\|)?\s*Page\s*(\d+))?(?:,\s*Section\s*['"]?([^'":\]]+)['"]?)?\]?:\s*(.*)/i
        );

        if (match) {
          if (match[2]) pageNum = parseInt(match[2], 10);
          if (match[3] && match[3].trim().toLowerCase() !== "none" && match[3].trim().toLowerCase() !== "null") {
            sectionName = match[3].trim();
          }
          mainContent = match[4] || "";
        } else {
          // Check for page number in string
          const pMatch = block.match(/Page\s*(\d+)/i);
          if (pMatch) pageNum = parseInt(pMatch[1], 10);
        }

        if (pageNum) {
          referredPages.add(pageNum);
        }

        const cleanedExcerpt = cleanText(mainContent).replace(/^[:\s\-]+/, "").replace(/\]\s*$/, "").trim();

        // If excerpt contains real substantive text (longer than 20 chars), preserve it
        if (cleanedExcerpt && cleanedExcerpt.length > 20 && !cleanedExcerpt.toLowerCase().startsWith("document passage")) {
          documentPassagesWithText.push({
            id: `document-${idx}-${bIdx}`,
            type: "document",
            label: "Document Extract",
            available: true,
            title: pageNum ? `Agreement Extract (Page ${pageNum})` : "Agreement Extract",
            page: pageNum,
            section: sectionName,
            items: [],
            excerpt: cleanedExcerpt,
          });
        }
      });
      return;
    }

    if (isGraph) {
      if (isUnavailable) {
        evidences.push({
          id: `graph-${idx}`,
          type: "knowledge_graph",
          label: "Knowledge Graph",
          available: false,
          items: ["No linked knowledge-graph relationships were available for this response."],
        });
        return;
      }

      const relations = trimmed
        .replace(/^###\s*\[SOURCE:[^\]]+\]/im, "")
        .split("\n")
        .map((l) => cleanText(l.replace(/^[-*•]\s*/, "")))
        .filter((l) => l && !l.startsWith("Status:"));

      if (relations.length > 0) {
        evidences.push({
          id: `graph-${idx}`,
          type: "knowledge_graph",
          label: "Knowledge Graph",
          available: true,
          title: "Entity Relationships",
          items: relations,
        });
      } else {
        evidences.push({
          id: `graph-${idx}`,
          type: "knowledge_graph",
          label: "Knowledge Graph",
          available: false,
          items: ["No linked knowledge-graph relationships were available for this response."],
        });
      }
      return;
    }

    // Generic fallback
    const cleanedGeneric = cleanText(trimmed);
    if (cleanedGeneric) {
      evidences.push({
        id: `generic-${idx}`,
        type: "generic",
        label: "Evidence",
        available: true,
        items: [cleanedGeneric],
      });
    }
  });

  // Consolidate document extracts
  if (documentPassagesWithText.length > 0) {
    evidences.push(...documentPassagesWithText);
  } else if (referredPages.size > 0) {
    // When no specific excerpt text was returned, show a single clean file reference card
    const sortedPages = Array.from(referredPages).sort((a, b) => Number(a) - Number(b));
    evidences.push({
      id: "document-ref-consolidated",
      type: "document",
      label: "Document Extract",
      available: true,
      title: "Credit Agreement & Ingested Filings",
      documentName: "Ingested SEC Filings & Credit Agreement",
      pages: sortedPages,
      items: [
        `Referred for verification across page${sortedPages.length > 1 ? "s" : ""} ${sortedPages.join(", ")}`,
      ],
    });
  }

  // Sort deterministically: financial -> document -> knowledge_graph -> generic
  const typeOrder: Record<string, number> = {
    financial: 1,
    document: 2,
    knowledge_graph: 3,
    generic: 4,
  };
  evidences.sort((a, b) => (typeOrder[a.type] || 99) - (typeOrder[b.type] || 99));

  const counts = {
    financial: evidences.filter((e) => e.type === "financial").length,
    document: evidences.filter((e) => e.type === "document").length,
    knowledge_graph: evidences.filter((e) => e.type === "knowledge_graph").length,
    total: evidences.length,
  };

  return { evidences, limitationNotice, counts };
}
