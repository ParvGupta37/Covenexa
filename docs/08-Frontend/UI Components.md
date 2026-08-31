# UI Components Reference

> Full design system in [Design System.md](./Design%20System.md).

## Shared Components (`src/components/shared/`)

### KpiCard
Displays a single metric with icon, value, change indicator, and optional badge.
```tsx
<KpiCard
  title="Portfolio Health"
  value="74"
  unit="/100"
  badge="GOOD"
  badgeVariant="success"
  change="+3 this month"
  icon={<HeartIcon />}
/>
```

### BorrowerCard
Displays a borrower tile with health score gauge and quick actions.

### AlertCard
Single alert row with severity icon (🔴/🟠/🟡/🔵), title, message, and timestamp.

### InfoTooltip
```tsx
<InfoTooltip content="Debt/EBITDA = Total Debt ÷ EBITDA. Higher = more leveraged." />
```
Renders a `ⓘ` icon; shows tooltip on hover.

### MetricExplainer
Inline label + tooltip for any financial metric on the page.

### ImprovedEmptyState
Full-card empty state with illustration, heading, description, and optional CTA button.

### LoadingSkeleton / CardSkeleton
Shimmer placeholder for async-loading content blocks.

### ErrorState
Error panel with retry button and error message.

## Layout Components (`src/components/layout/`)

### Sidebar
- Fixed left sidebar with navigation links
- Active route highlighted
- Covenexa logo + branding at top

### Topbar
- Borrower selector dropdown (`BORROWER: [name]`)
- User avatar + logout
- Mobile menu toggle

### AppLayout
Wraps all authenticated pages: `Sidebar + Topbar + main content area`
