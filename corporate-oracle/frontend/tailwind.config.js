/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        accent: '#00d4aa',
        accent2: '#3d8bfd',
        surface: {
          DEFAULT: '#111820',
          2: '#1a2332',
          3: '#0a0e14',
        },
      },
    },
  },
  plugins: [],
}
