/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#eef4ff",
          100: "#dbe7fe",
          400: "#5c8df6",
          500: "#3b6fe0",
          600: "#2c56c4",
          700: "#22439a",
        },
      },
    },
  },
  plugins: [],
};
