# Frontend Architecture

## Stack

| Technology | Version | Purpose |
|:-----------|:--------|:--------|
| React 18 | Latest | Component framework |
| TypeScript | ~5.x | Type safety |
| Vite | v5 | Dev server + bundler |
| Zustand | Latest | Global state management |
| React Router v6 | Latest | Client-side routing |
| Axios | Latest | HTTP client |
| Recharts | Latest | Charts (Donut, Bar, Sparkline) |
| Lucide React | Latest | Icon system |
| Vanilla CSS | Custom | Design system (`globals.css`) |

---

## Route Map

| Path | Component | Auth Required |
|:-----|:---------|:-------------|
| `/` | → redirects to `/login` or `/app` | No |
| `/login` | `LoginPage` | No |
| `/register` | `RegisterPage` | No |
| `/app` | `DashboardPage` | Yes |
| `/app/borrowers` | `BorrowersPage` | Yes |
| `/app/loans` | `LoansPage` | Yes |
| `/app/risk` | `RiskPage` | Yes |
| `/app/stress` | `StressTestPage` | Yes |
| `/app/graph` | `GraphPage` | Yes |
| `/app/documents` | `UploadsPage` | Yes |
| `/app/documents/:agreementId` | `DocumentDetailPage` | Yes |
| `/app/copilot` | `CopilotPage` | Yes |
| `/app/audit` | `AuditPage` | Yes |
| `/app/settings` | `OrganizationSettingsPage` | Yes (Admin) |

---

## Global State (Zustand)

### `auth.store.ts`
```typescript
{
  user: User | null,        // Logged-in user profile
  login(user, access_token, refresh_token): void,
  logout(): void,           // Clears localStorage tokens
}
```
Tokens persisted in `localStorage["access_token"]` and `localStorage["refresh_token"]`.

### `company.store.ts`
```typescript
{
  companies: Company[],           // All registered borrowers
  selectedCompanyId: string,      // Persisted in localStorage
  selectedCompany: Company | null,
  fetchCompanies(): Promise<void>,
  setSelectedCompanyId(id): void,
  registerCompany(data): Promise<Company>,
  clearCompanies(): void,         // Called on org deletion
}
```
Active borrower selection is persisted across page refreshes via `localStorage["selected_company_id"]`.

---

## Key Page Descriptions

### Dashboard (`/app`)
- Portfolio-wide KPI cards: Health Score, High Risk Borrowers, Covenants at Risk, Watchlist count
- Risk distribution donut chart (computed from live borrower data)
- Portfolio exposure bar chart (sum of loan principal amounts)
- Recent alerts feed (live from database)
- Top risky borrowers grid
- Dynamic AI Insight summary

### Risk Monitor (`/app/risk`)
- Borrower Health Score (0–100) with category badge
- Default probability with risk classification
- Financial ratios table (leverage, coverage, current ratio, gross margin)
- Active covenant compliance table (status, headroom)
- AI recommendations list

### Stress Testing (`/app/stress`)
- Revenue, EBITDA, Debt, Interest shock input sliders
- Submit scenario → shows projected health and default probability
- Breached covenants under stress scenario
- Comparison with current (unstressed) state

### Knowledge Graph (`/app/graph`)
- Interactive node-edge visualization
- Nodes: Borrower, Loan, Agreement, Covenant, FinancialMetric
- Edges: `HAS_LOAN`, `HAS_AGREEMENT`, `HAS_COVENANT`, `HAS_METRICS`
- Built from PostgreSQL (not Neo4j in v1.0)

### Documents (`/app/documents`)
- Upload PDF/DOCX with loan selection
- SEC EDGAR URL ingestion
- Document list with analysis status and pipeline progress
- Click document → `DocumentDetailPage`

### Document Detail (`/app/documents/:agreementId`)
- View extracted covenant list (name, threshold, operator)
- View extracted financial metrics by reporting period
- View raw document chunks

### AI Copilot (`/app/copilot`)
- Chat interface with streaming-style response
- Sends query + borrower_id → receives response + citations
- Citation cards showing source document chunks

---

## Component Architecture

### Shared Components (`src/components/shared/`)
- `KpiCard` — metric card with badge, trend, and sparkline
- `BorrowerCard` — borrower tile with health score gauge
- `AlertCard` — alert row with severity icon and timestamp
- `InfoTooltip` — `ⓘ` icon with hover tooltip
- `MetricExplainer` — inline label with tooltip for metrics
- `ImprovedEmptyState` — empty state card with action button
- `LoadingSkeleton` / `CardSkeleton` — shimmer placeholders
- `ErrorState` — retry-enabled error panel

### Layout Components (`src/components/layout/`)
- `Sidebar` — navigation links + active route highlighting
- `Topbar` — borrower selector dropdown (`BORROWER: [name]`) + user menu
- `AppLayout` — wraps all authenticated pages

---

## Axios Configuration (`src/lib/api.ts`)

```typescript
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000",
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) config.headers["Authorization"] = `Bearer ${token}`;
  return config;
});
```

---

## Design System

### Colors (Custom CSS Variables)
- Navy: `#111827` — primary text
- Indigo: `#7C8DFB` / `#4F46E5` — accent and interactive
- Light Gray: `#EEF1F5` — borders and backgrounds
- Success: `#10B981` | Warning: `#F97316` | Danger: `#EF4444`

### Typography
- Font: `Inter` (Google Fonts)
- Heading weights: 700–800
- Body: 400–600

### Card Pattern
```css
background: white;
border: 1px solid #EEF1F5;
border-radius: 16px;
box-shadow: 0 4px 20px rgba(17,24,39,0.04);
padding: 24px;
```
