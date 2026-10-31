/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        supaste: {
          bg: '#06080f',
          canvas: '#090d18',
          island: 'rgba(11, 15, 25, 0.88)',
          card: 'rgba(15, 22, 38, 0.72)',
          'card-hover': 'rgba(22, 32, 54, 0.82)',
          border: 'rgba(255, 255, 255, 0.1)',
          'border-light': 'rgba(255, 255, 255, 0.18)',
          accent: '#3b82f6',
          cyan: '#06b6d4',
          muted: '#94a3b8',
          subtle: '#64748b',
        },
        brand: {
          50: '#eff6ff',
          100: '#dbeafe',
          200: '#bfdbfe',
          300: '#93c5fd',
          400: '#60a5fa',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
          800: '#1e40af',
          900: '#1e3a8a',
          950: '#172554',
        },
      },
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'SF Pro Text', 'SF Pro Display', 'Segoe UI', 'Roboto', 'sans-serif'],
        mono: ['JetBrains Mono', 'SF Mono', 'Fira Code', 'Menlo', 'Monaco', 'monospace'],
      },
      boxShadow: {
        'island': '0 20px 45px -10px rgba(0, 0, 0, 0.65), 0 0 1px 1px rgba(255, 255, 255, 0.12) inset',
        'glass-card': '0 12px 32px -4px rgba(0, 0, 0, 0.5), 0 0 1px 1px rgba(255, 255, 255, 0.08) inset',
        'glow-blue': '0 0 25px -4px rgba(59, 130, 246, 0.35)',
        'glow-cyan': '0 0 25px -4px rgba(6, 182, 212, 0.35)',
      },
    },
  },
  plugins: [],
}
