
module.exports = {
  darkMode: false, // or 'media' or 'class'
  future: {
      removeDeprecatedGapUtilities: true,
      purgeLayersByDefault: true,
  },
  purge: {
      enabled: false, //true for production build
      content: [
          '**/templates/*.html',
          '**/templates/**/*.html'
      ]
  },
  theme: {
      extend: {},
  },
  variants: {},
  plugins: [],
}
