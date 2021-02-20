
module.exports = {
  darkMode: false, // or 'media' or 'class'
  future: {
      removeDeprecatedGapUtilities: true,
      purgeLayersByDefault: true,
  },
  purge: {
      enabled: true, // set to false for dev
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
