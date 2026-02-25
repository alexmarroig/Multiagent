/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        cyber: {
          cyan: '#00f3ff',
          magenta: '#ff00ff',
          yellow: '#f3ff00',
          blue: '#0066ff',
          red: '#ff0033',
          dark: '#05070a',
          card: 'rgba(10, 15, 26, 0.8)',
        },
      },
      animation: {
        'glow-pulse': 'glow-pulse 2s infinite',
        'scanline': 'scanline 8s linear infinite',
        'glitch': 'glitch 0.5s ease-in-out infinite',
        'spin-slow': 'spin 8s linear infinite',
        'float': 'float 6s ease-in-out infinite',
      },
      keyframes: {
        'glow-pulse': {
          '0%, 100%': { opacity: 0.8, filter: 'brightness(1)' },
          '50%': { opacity: 1, filter: 'brightness(1.5)' },
        },
        'scanline': {
          '0%': { transform: 'translateY(-100%)' },
          '100%': { transform: 'translateY(100%)' },
        },
        'glitch': {
          '0%, 100%': { transform: 'translate(0)' },
          '20%': { transform: 'translate(-2px, 2px)' },
          '40%': { transform: 'translate(-2px, -2px)' },
          '60%': { transform: 'translate(2px, 2px)' },
          '80%': { transform: 'translate(2px, -2px)' },
        },
        'float': {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-20px)' },
        },
      },
      backgroundImage: {
        'cyber-gradient': 'linear-gradient(180deg, #05070a 0%, #0a0f1a 100%)',
        'neon-conic': 'conic-gradient(from 180deg at 50% 50%, #00f3ff 0deg, #ff00ff 120deg, #00f3ff 360deg)',
      },
    },
  },
  plugins: [],
}
