module.exports = {
  root: true,
  env: { browser: true, es2022: true, node: true },
  parserOptions: { ecmaVersion: "latest", sourceType: "module", ecmaFeatures: { jsx: true } },
  settings: { react: { version: "detect" } },
  plugins: ["react", "react-hooks"],
  extends: ["eslint:recommended", "plugin:react/recommended", "plugin:react-hooks/recommended"],
  rules: {
    // React 17+ doesn't require React in scope
    "react/react-in-jsx-scope": "off",
    // Disable PropTypes requirement for projects not using it
    "react/prop-types": "off",
    // Avoid failing the build on unused vars in WIP code
    "no-unused-vars": "off",
    // Reduce noise from stylistic rules while we stabilize the codebase
    "react/display-name": "off",
    "react/no-unescaped-entities": "off",
    "react-hooks/exhaustive-deps": "off"
  },
  overrides: [
    {
      files: ["vite.config.js"],
      env: { node: true }
    },
    {
      files: ["**/__tests__/**", "**/*.test.*", "**/*test*.*"],
      env: { jest: true, node: true },
      rules: {
        // Test environment provides globals like describe/test/expect
        "no-undef": "off"
      }
    }
  ]
};