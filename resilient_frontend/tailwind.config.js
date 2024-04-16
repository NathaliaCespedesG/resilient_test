/** @type {import('tailwindcss').Config} */

import animations from '@midudev/tailwind-animations'

module.exports = {
  content: ["./src/**/*.{html,js}"],
  theme: {
    extend: {},
  },
  corePlugins: {    preflight: false,  },
  plugins: [require('@tailwindcss/forms'), animations],
}

