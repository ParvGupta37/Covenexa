# Design System

## Philosophy

Covenexa's design system is built on vanilla CSS with custom properties (CSS variables). No utility class frameworks. Full control over every pixel.

---

## Color Palette

```css
:root {
  /* Primary Background */
  --color-bg-primary: #F8F9FC;
  --color-bg-card: #FFFFFF;

  /* Text */
  --color-text-primary: #111827;
  --color-text-secondary: #6B7280;
  --color-text-muted: #9CA3AF;

  /* Brand */
  --color-indigo: #4F46E5;
  --color-indigo-light: #7C8DFB;
  --color-indigo-hover: #4338CA;

  /* Status */
  --color-success: #10B981;
  --color-warning: #F97316;
  --color-danger: #EF4444;
  --color-info: #3B82F6;

  /* Borders */
  --color-border: #EEF1F5;
  --color-border-strong: #D1D5DB;

  /* Severity badges */
  --color-critical-bg: #FEF2F2;
  --color-critical-text: #DC2626;
  --color-high-bg: #FFF7ED;
  --color-high-text: #EA580C;
  --color-medium-bg: #FFFBEB;
  --color-medium-text: #D97706;
  --color-low-bg: #F0FDF4;
  --color-low-text: #16A34A;
}
```

---

## Typography

```css
/* Google Fonts: Inter */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  font-size: 14px;
  color: var(--color-text-primary);
}

/* Scale */
h1 { font-size: 28px; font-weight: 800; }
h2 { font-size: 22px; font-weight: 700; }
h3 { font-size: 18px; font-weight: 600; }
.label { font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; }
.metric { font-size: 32px; font-weight: 800; }
```

---

## Card Component

```css
.card {
  background: white;
  border: 1px solid var(--color-border);
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(17, 24, 39, 0.04);
  padding: 24px;
}
```

---

## Badge / Status Pill

```css
.badge {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  border-radius: 9999px;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.badge--critical { background: var(--color-critical-bg); color: var(--color-critical-text); }
.badge--high     { background: var(--color-high-bg);     color: var(--color-high-text);     }
.badge--medium   { background: var(--color-medium-bg);   color: var(--color-medium-text);   }
.badge--low      { background: var(--color-low-bg);      color: var(--color-low-text);      }
```

---

## Spacing Scale

| Token | Value |
|:------|:------|
| `--space-xs` | 4px |
| `--space-sm` | 8px |
| `--space-md` | 16px |
| `--space-lg` | 24px |
| `--space-xl` | 32px |
| `--space-2xl` | 48px |

---

## Border Radius

| Usage | Value |
|:------|:------|
| Cards | 16px |
| Buttons | 10px |
| Pills / Badges | 9999px (fully rounded) |
| Inputs | 8px |
