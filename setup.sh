#!/bin/bash

set -e

PROJECT_NAME="Covenexa"

echo "======================================"
echo "Setting up $PROJECT_NAME..."
echo "======================================"

# --------------------------------------------------
# Root Project Structure
# --------------------------------------------------

mkdir -p "$PROJECT_NAME"

cd "$PROJECT_NAME"

mkdir -p \
frontend \
backend \
agents \
orchestration \
knowledge-graph \
rag-engine \
financial-engine \
compliance-engine \
recommendation-engine \
reporting-engine \
monitoring \
infrastructure \
docs

touch README.md

echo "✓ Root project structure created."

# --------------------------------------------------
# Documentation Directories
# --------------------------------------------------

mkdir -p \
docs/00-Overview \
docs/01-Business \
docs/02-System-Architecture \
docs/03-Technology-Stack \
docs/04-Database-Design \
docs/05-AI-Architecture \
docs/06-Multi-Agent-System \
docs/07-Backend \
docs/08-Frontend \
docs/09-Security \
docs/10-DevOps \
docs/11-Testing \
docs/12-Implementation \
docs/13-Portfolio \
docs/14-Research

touch docs/README.md

echo "✓ Documentation directories created."

echo ""
echo "Creating documentation files..."
echo ""


# --------------------------------------------------
# 00 - Overview
# --------------------------------------------------

touch \
docs/00-Overview/"Vision.md" \
docs/00-Overview/"Problem Statement.md" \
docs/00-Overview/"PRD.md" \
docs/00-Overview/"Product Roadmap.md" \
docs/00-Overview/"Terminology.md"

# --------------------------------------------------
# 01 - Business
# --------------------------------------------------

touch \
docs/01-Business/"Industry Overview.md" \
docs/01-Business/"Private Credit Explained.md" \
docs/01-Business/"Customer Personas.md" \
docs/01-Business/"User Journey.md" \
docs/01-Business/"Competitive Analysis.md"

# --------------------------------------------------
# 02 - System Architecture
# --------------------------------------------------

touch \
docs/02-System-Architecture/"High Level Architecture.md" \
docs/02-System-Architecture/"Service Architecture.md" \
docs/02-System-Architecture/"Event Flow.md" \
docs/02-System-Architecture/"Agent Communication.md" \
docs/02-System-Architecture/"Deployment Architecture.md" \
docs/02-System-Architecture/"Sequence Diagrams.md"

# --------------------------------------------------
# 03 - Technology Stack
# --------------------------------------------------

touch \
docs/03-Technology-Stack/"Frontend.md" \
docs/03-Technology-Stack/"Backend.md" \
docs/03-Technology-Stack/"AI Stack.md" \
docs/03-Technology-Stack/"Database Stack.md" \
docs/03-Technology-Stack/"Infrastructure.md" \
docs/03-Technology-Stack/"Technology Decisions.md"

echo "✓ Overview, Business, Architecture and Technology docs created."


# --------------------------------------------------
# 04 - Database Design
# --------------------------------------------------

touch \
docs/04-Database-Design/"PostgreSQL Schema.md" \
docs/04-Database-Design/"Neo4j Schema.md" \
docs/04-Database-Design/"Vector Database.md" \
docs/04-Database-Design/"Object Storage.md" \
docs/04-Database-Design/"ER Diagram.md" \
docs/04-Database-Design/"Data Models.md"

# --------------------------------------------------
# 05 - AI Architecture
# --------------------------------------------------

touch \
docs/05-AI-Architecture/"RAG Pipeline.md" \
docs/05-AI-Architecture/"Knowledge Graph.md" \
docs/05-AI-Architecture/"Embeddings.md" \
docs/05-AI-Architecture/"Prompt Engineering.md" \
docs/05-AI-Architecture/"Context Management.md" \
docs/05-AI-Architecture/"Guardrails.md" \
docs/05-AI-Architecture/"AI Evaluation.md"

# --------------------------------------------------
# 06 - Multi-Agent System
# --------------------------------------------------

touch \
docs/06-Multi-Agent-System/"Planner Agent.md" \
docs/06-Multi-Agent-System/"Document Agent.md" \
docs/06-Multi-Agent-System/"Covenant Agent.md" \
docs/06-Multi-Agent-System/"Financial Agent.md" \
docs/06-Multi-Agent-System/"Compliance Agent.md" \
docs/06-Multi-Agent-System/"Portfolio Agent.md" \
docs/06-Multi-Agent-System/"Recommendation Agent.md" \
docs/06-Multi-Agent-System/"Copilot Agent.md" \
docs/06-Multi-Agent-System/"Reporting Agent.md" \
docs/06-Multi-Agent-System/"Monitoring Agent.md" \
docs/06-Multi-Agent-System/"Shared Memory.md" \
docs/06-Multi-Agent-System/"Agent Communication.md"

echo "✓ Database, AI Architecture and Multi-Agent docs created."


# --------------------------------------------------
# 07 - Backend
# --------------------------------------------------

touch \
docs/07-Backend/"API Design.md" \
docs/07-Backend/"Authentication.md" \
docs/07-Backend/"Authorization.md" \
docs/07-Backend/"Event Bus.md" \
docs/07-Backend/"Workers.md" \
docs/07-Backend/"WebSockets.md" \
docs/07-Backend/"Background Jobs.md"

# --------------------------------------------------
# 08 - Frontend
# --------------------------------------------------

touch \
docs/08-Frontend/"Dashboard.md" \
docs/08-Frontend/"Portfolio View.md" \
docs/08-Frontend/"Borrower View.md" \
docs/08-Frontend/"Agreement Viewer.md" \
docs/08-Frontend/"AI Chat.md" \
docs/08-Frontend/"Risk Analytics.md" \
docs/08-Frontend/"UI Components.md" \
docs/08-Frontend/"Design System.md"

# --------------------------------------------------
# 09 - Security
# --------------------------------------------------

touch \
docs/09-Security/"RBAC.md" \
docs/09-Security/"Encryption.md" \
docs/09-Security/"Audit Logs.md" \
docs/09-Security/"Compliance.md" \
docs/09-Security/"Secrets Management.md"

# --------------------------------------------------
# 10 - DevOps
# --------------------------------------------------

touch \
docs/10-DevOps/"Docker.md" \
docs/10-DevOps/"Kubernetes.md" \
docs/10-DevOps/"CI-CD.md" \
docs/10-DevOps/"Monitoring.md" \
docs/10-DevOps/"Logging.md" \
docs/10-DevOps/"Scaling.md"

# --------------------------------------------------
# 11 - Testing
# --------------------------------------------------

touch \
docs/11-Testing/"Unit Tests.md" \
docs/11-Testing/"Integration Tests.md" \
docs/11-Testing/"Agent Tests.md" \
docs/11-Testing/"Evaluation Benchmarks.md" \
docs/11-Testing/"Performance Tests.md"

# --------------------------------------------------
# 12 - Implementation
# --------------------------------------------------

touch \
docs/12-Implementation/"Sprint-1.md" \
docs/12-Implementation/"Sprint-2.md" \
docs/12-Implementation/"Sprint-3.md" \
docs/12-Implementation/"Sprint-4.md" \
docs/12-Implementation/"Deployment Checklist.md"

# --------------------------------------------------
# 13 - Portfolio
# --------------------------------------------------

touch \
docs/13-Portfolio/"Case Study.md" \
docs/13-Portfolio/"Demo Script.md" \
docs/13-Portfolio/"Resume Points.md" \
docs/13-Portfolio/"Architecture Images.md" \
docs/13-Portfolio/"Screenshots.md"

# --------------------------------------------------
# 14 - Research
# --------------------------------------------------

touch \
docs/14-Research/"Private Credit Notes.md" \
docs/14-Research/"Financial Concepts.md" \
docs/14-Research/"Covenant Examples.md" \
docs/14-Research/"Loan Agreement Samples.md" \
docs/14-Research/"LLM Research.md" \
docs/14-Research/"Knowledge Graph Research.md" \
docs/14-Research/"Agentic AI Research.md" \
docs/14-Research/"RAG Research.md" \
docs/14-Research/"Ideas.md" \
docs/14-Research/"Future Improvements.md"

echo ""
echo "======================================"
echo "✅ Covenexa project structure created!"
echo "======================================"
echo ""
echo "Project Location: $(pwd)"
echo ""
echo "Next Steps:"
echo "1. code ."
echo "2. Initialize Git:"
echo "   git init"
echo "3. Open docs/README.md and begin Phase 1."
echo ""