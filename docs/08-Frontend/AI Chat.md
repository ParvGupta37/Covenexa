# AI Copilot — Chat Interface

> Full frontend documentation in [Dashboard.md](./Dashboard.md).

## Page: `/app/copilot`

The AI Copilot page provides a conversational interface for querying borrower data.

### UI Structure
- Chat history panel (scrollable message list)
- User messages (right-aligned, indigo background)
- AI responses (left-aligned, white card)
- Citation cards below each AI response
- Input bar with send button (Enter to send)
- Borrower context shown in top bar

### Request Flow
```
User types query → POST /api/v1/copilot/query
  Body: { query, borrower_id }
  → Wait for response (~2–5 seconds with Cohere API)
  → Display response + citation list
```

### State Management
- Messages stored in local component state (not Zustand)
- Session not persisted across page refreshes (v1.0)
- `selectedCompany.id` from company.store used as borrower_id
