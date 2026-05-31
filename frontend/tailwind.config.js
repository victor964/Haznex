/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "../backend/store/templates/**/*.html",
    "../backend/accounts/templates/**/*.html",
    "../backend/orders/templates/**/*.html",
    "../backend/payments/templates/**/*.html",
    "../backend/admin_panel/templates/**/*.html",
  ],
  theme: {
    extend: {
      colors: {
        gold: {
          DEFAULT: "#c9a227",
          dark: "#a68521",
          light: "#e8d48a",
        },
        haznex: {
          bg: "#f8f7f4",
          border: "#e8e4da",
          muted: "#6b6b6b",
          text: "#1a1a1a",
        },
      },
      fontFamily: {
        sans: ["Inter", "Segoe UI", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};
