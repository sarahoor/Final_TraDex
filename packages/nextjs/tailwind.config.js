/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx}",
    "./components/**/*.{js,ts,jsx,tsx}",
    "./app/**/*.{js,ts,jsx,tsx}",
    "./packages/nextjs/**/*.{js,ts,jsx,tsx}", // if using monorepo (Scaffold-ETH 2 style)
  ],
  theme: {
    extend: {},
  },
  plugins: [],
};
