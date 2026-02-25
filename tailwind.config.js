/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './apps/web/app/**/*.{js,ts,jsx,tsx,mdx}',
    './apps/web/components/**/*.{js,ts,jsx,tsx,mdx}',
    './apps/web/src/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        neutralDark: {
          50: '#1A1A1A',
          100: '#0A0A0A',
          200: '#111111',
          300: '#171717',
        },
        primary: '#3A82F7',
        secondary: '#F59E0B',
        success: '#10B981',
        danger: '#EF4444',
      },
    },
  },
  plugins: [],
};
