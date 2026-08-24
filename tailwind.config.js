/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        network: {
          ink: "#10231b",
          muted: "#65736b",
          brand: "#0f766e",
          accent: "#f59e0b",
        },
      },
      fontFamily: {
        sans: ["Aptos", "Segoe UI Variable", "Trebuchet MS", "sans-serif"],
        mono: ["Cascadia Mono", "JetBrains Mono", "SFMono-Regular", "Consolas", "monospace"],
      },
      boxShadow: {
        panel: "0 8px 24px rgba(24, 44, 36, 0.08)",
      },
    },
  },
  plugins: [],
};
