/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./cogip/tools/**/static/js/*.js",
    "./cogip/tools/**/templates/*.html",
  ],
  theme: {
    extend: {
      colors: {
        "grey-color": "var(--grey-color)",
        "red-cogip": "var(--red-cogip)",
        "camp-1": "var(--color-camp-1)",
        "camp-2": "var(--color-camp-2)",
        "custom-button": "hsla(0, 0%, 30%, 0.56)",
      },
      height: {
        "10p": "10%",
        "minus-footer": "calc(100vh - 55px)",
      },
      fontSize: {
        "1500p": "1500%",
      },
      transitionProperty: {
        bottom: "bottom",
      },
      transitionDuration: {
        400: "400ms",
      },
      zIndex: {
        100: "100",
      },
    },
  },
  content: [
    "./cogip/tools/**/static/js/*.js",
    "./cogip/tools/**/templates/*.html",
  ],
  safelist: ["bg-camp-1", "bg-camp-2", "border-camp-1", "border-camp-2"],
  plugins: ["postcss-import", "tailwindcss", "autoprefixer"],
};

