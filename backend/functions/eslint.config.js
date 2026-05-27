module.exports = [
  {
    ignores: ["node_modules/**"]
  },
  {
    files: ["**/*.js"],
    languageOptions: {
      ecmaVersion: 2022,
      sourceType: "commonjs",
      globals: {
        console: "readonly",
        module: "readonly",
        require: "readonly",
        exports: "readonly",
        process: "readonly",
        __dirname: "readonly",
        Buffer: "readonly",
        URL: "readonly",
        fetch: "readonly"
      }
    },
    rules: {
      "no-unused-vars": ["error", { argsIgnorePattern: "^_" }],
      "no-undef": "error",
      semi: ["error", "always"],
      quotes: ["error", "double"]
    }
  }
];
