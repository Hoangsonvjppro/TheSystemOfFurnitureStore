/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{html,js}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#3b82f6', // blue-500
          50: '#eff6ff',      // blue-50
          100: '#dbeafe',     // blue-100
          200: '#bfdbfe',     // blue-200
          300: '#93c5fd',     // blue-300
          400: '#60a5fa',     // blue-400
          500: '#3b82f6',     // blue-500
          600: '#2563eb',     // blue-600
          700: '#1d4ed8',     // blue-700
          800: '#1e40af',     // blue-800
          900: '#1e3a8a',     // blue-900
        },
        secondary: {
          DEFAULT: '#10b981', // emerald-500
          50: '#ecfdf5',      // emerald-50
          100: '#d1fae5',     // emerald-100
          200: '#a7f3d0',     // emerald-200
          300: '#6ee7b7',     // emerald-300
          400: '#34d399',     // emerald-400
          500: '#10b981',     // emerald-500
          600: '#059669',     // emerald-600
          700: '#047857',     // emerald-700
          800: '#065f46',     // emerald-800
          900: '#064e3b',     // emerald-900
        },
        accent: {
          DEFAULT: '#f59e0b', // amber-500
          50: '#fffbeb',      // amber-50
          100: '#fef3c7',     // amber-100
          200: '#fde68a',     // amber-200
          300: '#fcd34d',     // amber-300
          400: '#fbbf24',     // amber-400
          500: '#f59e0b',     // amber-500
          600: '#d97706',     // amber-600
          700: '#b45309',     // amber-700
          800: '#92400e',     // amber-800
          900: '#78350f',     // amber-900
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        serif: ['Merriweather', 'Georgia', 'serif'],
      },
      spacing: {
        '128': '32rem',
        '144': '36rem',
      },
      borderRadius: {
        '4xl': '2rem',
      },
      boxShadow: {
        'card': '0 5px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
      }
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
    require('@tailwindcss/aspect-ratio'),
  ],
}
