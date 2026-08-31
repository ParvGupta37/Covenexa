import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: [
    "./pages/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./app/**/*.{ts,tsx}",
    "./src/**/*.{ts,tsx}",
  ],
  theme: {
    container: {
      center: true,
      padding: "2rem",
      screens: {
        "2xl": "1400px",
      },
    },
    extend: {
      colors: {
        border: "var(--border)",
        input: "var(--input)",
        ring: "var(--ring)",
        background: "var(--background)",
        foreground: "var(--foreground)",
        brand: {
          50: "#F3F4FF",
          100: "#E8ECFF",
          200: "#C7D2FE",
          500: "#7C8DFB",
          600: "#6366F1",
          700: "#4F46E5",
        },
        risk: {
          high: {
            bg: "#FEE2E2",
            text: "#EF4444",
            border: "#FCA5A5",
          },
          watch: {
            bg: "#FFEDD5",
            text: "#F97316",
            border: "#FDBA74",
          },
          moderate: {
            bg: "#FEF3C7",
            text: "#D97706",
            border: "#FDE68A",
          },
          low: {
            bg: "#D1FAE5",
            text: "#10B981",
            border: "#6EE7B7",
          },
        },
        primary: {
          DEFAULT: "var(--primary)",
          foreground: "var(--primary-foreground)",
        },
        secondary: {
          DEFAULT: "var(--secondary)",
          foreground: "var(--secondary-foreground)",
        },
        destructive: {
          DEFAULT: "var(--destructive)",
          foreground: "var(--destructive-foreground)",
        },
        muted: {
          DEFAULT: "var(--muted)",
          foreground: "var(--muted-foreground)",
        },
        accent: {
          DEFAULT: "var(--accent)",
          foreground: "var(--accent-foreground)",
        },
        popover: {
          DEFAULT: "var(--popover)",
          foreground: "var(--popover-foreground)",
        },
        card: {
          DEFAULT: "var(--card)",
          foreground: "var(--card-foreground)",
        },
      },
      boxShadow: {
        card: "0 4px 20px rgba(17, 24, 39, 0.05)",
        "card-hover": "0 8px 30px rgba(17, 24, 39, 0.08)",
        dropdown: "0 10px 40px rgba(17, 24, 39, 0.12)",
      },
      borderRadius: {
        card: "18px",
        btn: "12px",
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      fontFamily: {
        sans: ["Inter", "-apple-system", "BlinkMacSystemFont", "sans-serif"],
      },
      keyframes: {
        "accordion-down": {
          from: { height: "0" },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: "0" },
        },
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
};

export default config;
