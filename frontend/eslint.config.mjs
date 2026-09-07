import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";

const eslintConfig = defineConfig([
  ...nextVitals,
  ...nextTs,
  {
    rules: {
      // Gradual-typing debt, not correctness. ~150 sites; tracked as
      // warnings so `eslint` still exits 0 while they get chipped away.
      "@typescript-eslint/no-explicit-any": "warn",
      // Cosmetic - a literal apostrophe in JSX text renders fine.
      "react/no-unescaped-entities": "warn",
      // Useful signal, but blanket-"fixing" a dep array can introduce
      // render loops - each one needs judgment, so: warn, not error.
      "react-hooks/exhaustive-deps": "warn",
      // Experimental React-Compiler adoption rule. In this codebase it
      // flags standard patterns (e.g. e.preventDefault() in a handler),
      // so it's advisory until the compiler is actually adopted.
      "react-hooks/immutability": "warn",
      "react-hooks/preserve-manual-memoization": "warn",
    },
  },
  // Override default ignores of eslint-config-next.
  globalIgnores([
    ".next/**",
    "out/**",
    "build/**",
    "next-env.d.ts",
  ]),
]);

export default eslintConfig;
