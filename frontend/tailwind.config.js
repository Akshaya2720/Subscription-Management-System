/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        apple: {
          canvas: '#f5f5f7',
          card: '#ffffff',
          text: '#1d1d1f',
          subtext: '#6e6e73',
          border: '#d2d2d7',
          'border-light': 'rgba(0, 0, 0, 0.08)',
          blue: '#0071e3',
          'blue-hover': '#0077ed',
          'blue-active': '#0062c4',
          gray: '#e8e8ed',
          'gray-hover': '#dcdce2',
          pill: '#f5f5f7',
        },
        brand: {
          50: '#f0f7ff',
          100: '#e0effe',
          200: '#bae0fd',
          300: '#7cc5fb',
          400: '#38a5f8',
          500: '#0071e3', // Apple Blue
          600: '#0071e3',
          700: '#005bbf',
          800: '#074c9c',
          900: '#0c407f',
          950: '#082852',
        },
      },
      fontFamily: {
        sans: [
          '-apple-system',
          'BlinkMacSystemFont',
          'SF Pro Text',
          'SF Pro Display',
          'Inter',
          'Helvetica Neue',
          'Segoe UI',
          'Roboto',
          'sans-serif'
        ],
        mono: ['SF Mono', 'JetBrains Mono', 'Menlo', 'Monaco', 'monospace'],
      },
      boxShadow: {
        'apple-sm': '0 2px 8px rgba(0, 0, 0, 0.04)',
        'apple-card': '0 4px 20px rgba(0, 0, 0, 0.04)',
        'apple-floating': '0 8px 30px rgba(0, 0, 0, 0.08)',
        'glass-card': '0 2px 14px rgba(0, 0, 0, 0.04)',
        'island': '0 4px 24px rgba(0, 0, 0, 0.06)',
        'glow-blue': '0 2px 10px rgba(0, 113, 227, 0.25)',
      },
    },
  },
  plugins: [],
}
