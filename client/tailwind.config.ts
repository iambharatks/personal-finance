import type { Config } from "tailwindcss";

// Colours are CSS variables (src/index.css) so light and dark swap in one place.
const token = (name: string) => `rgb(var(--${name}) / <alpha-value>)`;

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        page: token("page"),
        surface: token("surface"),
        ink: token("ink"),
        "ink-2": token("ink-2"),
        muted: token("muted"),
        line: token("line"),
        sidebar: "#0f172a",
      },
    },
  },
  plugins: [],
} satisfies Config;
