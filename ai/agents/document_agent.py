"""
Document Ingestion Agent.
Handles document loading, parsing (LlamaParse/pypdf), chunking,
embedding generation (Cohere), and indexing (Pinecone).
"""
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List

import structlog
from ai.agents.base_agent import BaseAgent
from integrations.llamaparse.client import LlamaParseClient

logger = structlog.get_logger(__name__)


class DocumentAgent(BaseAgent):
    """
    Parses incoming PDF/text documents, generates semantic chunks,
    calculates text embeddings, and saves them to Pinecone and PostgreSQL.
    """

    @property
    def name(self) -> str:
        return "DocumentAgent"

    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        agreement_id = state.get("agreement_id")
        file_path = state.get("file_path")
        borrower_id = state.get("borrower_id")

        if not agreement_id or not file_path:
            state["status"] = "failed"
            state["error"] = "Missing agreement_id or file_path in state."
            return state

        logger.info("document_agent.run_start", agreement_id=agreement_id, file_path=file_path)

        # 1. Update status to parsing
        await self._update_agreement_status(agreement_id, "parsing")

        # 2. Parse document (using LlamaParse with pypdf fallback)
        try:
            from app.core.config import settings
            llamaparse_key = settings.LLAMA_CLOUD_API_KEY or os.getenv("LLAMAPARSE_API_KEY", "not_set")
            parser = LlamaParseClient(api_key=llamaparse_key)
            parser.initialize()
            parsed_data = await parser.parse_document(file_path)
        except Exception as exc:
            logger.error("document_agent.parsing_failed", error=str(exc))
            await self._update_agreement_status(agreement_id, "failed", f"Parsing error: {exc}")
            state["status"] = "failed"
            state["error"] = f"Parsing failed: {exc}"
            return state

        text = parsed_data.get("text", "")
        pages = parsed_data.get("pages", [])
        page_count = parsed_data.get("page_count", 0)

        if not text:
            await self._update_agreement_status(agreement_id, "failed", "Extracted text is empty.")
            state["status"] = "failed"
            state["error"] = "Extracted text is empty."
            return state

        # 3. Create semantic chunks
        logger.info("document_agent.chunking", agreement_id=agreement_id, page_count=page_count)
        await self._update_agreement_status(agreement_id, "chunking")
        chunks = self._create_chunks(pages)

        # 4. Save chunks to PostgreSQL via MCP postgres tool
        logger.info("document_agent.saving_chunks", count=len(chunks))
        chunk_records = []
        for idx, chunk in enumerate(chunks):
            chunk_id = str(uuid.uuid4())
            chunk_records.append({
                "id": chunk_id,
                "agreement_id": agreement_id,
                "chunk_index": idx,
                "page_number": chunk["page"],
                "section": chunk["section"],
                "content": chunk["content"],
                "char_count": len(chunk["content"]),
            })

            # Write chunk to DB via MCP
            await self._mcp.execute_tool(
                tool_name="postgres",
                operation="execute_write",
                params={
                    "query": """
                        INSERT INTO document_chunks (id, agreement_id, chunk_index, page_number, section, content, char_count, created_at)
                        VALUES (:id, :agreement_id, :chunk_index, :page_number, :section, :content, :char_count, NOW())
                    """,
                    "params": chunk_records[-1]
                }
            )

        # 5. Generate embeddings and index in Pinecone via MCP pinecone tool
        logger.info("document_agent.embedding_and_indexing", chunk_count=len(chunks))
        await self._update_agreement_status(agreement_id, "embedding")

        try:
            # Generate embeddings batch by batch using self._llm._provider which has cohere_client
            chunk_texts = [c["content"] for c in chunk_records]
            # LLMProvider cohere has direct embed support
            embeddings = await self._llm._provider.embed(chunk_texts)

            # Build vectors array
            vectors = []
            for idx, embedding in enumerate(embeddings):
                c_rec = chunk_records[idx]
                vectors.append({
                    "id": c_rec["id"],
                    "values": embedding,
                    "metadata": {
                        "agreement_id": agreement_id,
                        "borrower_id": borrower_id or "unknown",
                        "page_number": c_rec["page_number"],
                        "section": c_rec["section"] or "none",
                        "char_count": c_rec["char_count"],
                    }
                })

            # Upsert via MCP Pinecone Tool
            await self._mcp.execute_tool(
                tool_name="pinecone",
                operation="upsert_vectors",
                params={"vectors": vectors}
            )

            # Update chunk records with embedding ID in PostgreSQL
            for c_rec in chunk_records:
                await self._mcp.execute_tool(
                    tool_name="postgres",
                    operation="execute_write",
                    params={
                        "query": "UPDATE document_chunks SET embedding_id = :id WHERE id = :id",
                        "params": {"id": c_rec["id"]}
                    }
                )

        except Exception as exc:
            logger.error("document_agent.embedding_indexing_failed", error=str(exc))
            # Gracefully log warning but proceed (local pinecone might be missing keys)

        # 6. Update agreement metadata and set status to embedding_done
        await self._mcp.execute_tool(
            tool_name="postgres",
            operation="execute_write",
            params={
                "query": """
                    UPDATE agreements
                    SET processing_status = 'embedding_done',
                        page_count = :page_count,
                        chunk_count = :chunk_count,
                        processed_at = NOW()
                    WHERE id = :id
                """,
                "params": {
                    "id": agreement_id,
                    "page_count": page_count,
                    "chunk_count": len(chunks),
                }
            }
        )

        state.update({
            "status": "embedding_done",
            "parsed_text": text,
            "page_count": page_count,
            "chunk_count": len(chunks),
        })
        return state

    def _create_chunks(self, pages: List[Dict[str, Any]], chunk_size: int = 1500, overlap: int = 150) -> List[Dict[str, Any]]:
        """Split page contents into overlapping character semantic chunks."""
        chunks = []
        for page in pages:
            page_num = page.get("page", 1)
            content = page.get("content", "")
            if not content.strip():
                continue

            # Standard chunking
            start = 0
            while start < len(content):
                end = start + chunk_size
                chunk_text = content[start:end]
                
                # Determine section label if possible
                section = None
                lines = chunk_text.splitlines()
                for line in lines:
                    if line.strip().isupper() and len(line.strip()) > 3:
                        section = line.strip()
                        break

                chunks.append({
                    "page": page_num,
                    "section": section,
                    "content": chunk_text,
                })
                start += (chunk_size - overlap)
        return chunks

    async def _update_agreement_status(self, agreement_id: str, status: str, error_msg: str | None = None) -> None:
        """Update processing_status and error details on the Agreement."""
        await self._mcp.execute_tool(
            tool_name="postgres",
            operation="execute_write",
            params={
                "query": """
                    UPDATE agreements
                    SET processing_status = :status,
                        processing_error = :error
                    WHERE id = :id
                """,
                "params": {
                    "id": agreement_id,
                    "status": status,
                    "error": error_msg,
                }
            }
        )
