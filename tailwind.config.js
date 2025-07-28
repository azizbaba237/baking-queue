/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class', 
  content: [
    "./templates/**/*.html",
    "./*/templates/**/*.html",
    "./static/js/**/*.js",
  ],
  theme: {
    extend: {
      colors: {
        'bank': {
          blue: '#1E40AF',
          'dark-blue': '#1e3a8a',        // plus foncé pour le mode sombre
          'light-blue': '#3B82F6',
          gold: '#F59E0B',
          'dark-gold': '#b38f00',
          'light-gold': '#FCD34D',
          gray: '#6B7280',
          'light-gray': '#F3F4F6',
          'dark-gray': '#374151',
          'darker-gray': '#1F2937',
          green: '#10B981',
          red: '#EF4444',
          orange: '#F97316',
        }
      },
      fontFamily: {
        'bank': ['Inter', 'sans-serif'],
      },
      spacing: {
        '72': '18rem',
        '84': '21rem',
        '96': '24rem',
      },
      animation: {
        'pulse-slow': 'pulse 3s infinite',
        'bounce-slow': 'bounce 2s infinite',
      }
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
  ],
}

