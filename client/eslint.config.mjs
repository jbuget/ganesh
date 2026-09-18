import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";
import boundaries from "eslint-plugin-boundaries";

const eslintConfig = defineConfig([
  ...nextVitals,
  ...nextTs,

  // --- Atomic Design: the composition rules become errors -------------------
  {
    plugins: { boundaries },
    settings: {
      "boundaries/elements": [
        { type: "ui", pattern: "src/components/ui", partialMatch: true },
        { type: "atoms", pattern: "src/components/atoms", partialMatch: true },
        { type: "molecules", pattern: "src/components/molecules", partialMatch: true },
        { type: "organisms", pattern: "src/components/organisms", partialMatch: true },
        { type: "app", pattern: "src/app/**" },
        { type: "lib", pattern: "src/lib/**" },
      ],
      "boundaries/files": [
        { category: "test", pattern: "**/*.{test,spec}.{ts,tsx}" },
      ],
    },
    rules: {
      "boundaries/dependencies": [
        "error",
        {
          default: "disallow",
          policies: [
            // npm packages stay free.
            { allow: { to: { module: { origin: "external" } } } },
            // A test file may import the component it checks.
            {
              from: { file: { categories: "test" } },
              allow: {
                to: {
                  element: {
                    types: {
                      anyOf: [
                        "ui",
                        "atoms",
                        "molecules",
                        "organisms",
                        "app",
                        "lib",
                      ],
                    },
                  },
                },
              },
            },
            // An atom never imports another local component.
            {
              from: { element: { type: "atoms" } },
              allow: { to: { element: { types: { anyOf: ["ui", "lib"] } } } },
            },
            // A molecule imports atoms only.
            {
              from: { element: { type: "molecules" } },
              allow: {
                to: { element: { types: { anyOf: ["atoms", "ui", "lib"] } } },
              },
            },
            // An organism may import atoms and molecules, and compose another
            // organism: a page assembles sections.
            {
              from: { element: { type: "organisms" } },
              allow: {
                to: {
                  element: {
                    types: {
                      anyOf: ["atoms", "molecules", "organisms", "ui", "lib"],
                    },
                  },
                },
              },
            },
            // Pages import organisms only.
            {
              from: { element: { type: "app" } },
              allow: {
                to: { element: { types: { anyOf: ["organisms", "lib", "app"] } } },
              },
            },
            {
              from: { element: { type: "lib" } },
              allow: { to: { element: { type: "lib" } } },
            },
            {
              from: { element: { type: "ui" } },
              allow: { to: { element: { types: { anyOf: ["ui", "lib"] } } } },
            },
          ],
        },
      ],
    },
  },

  globalIgnores([
    ".next/**",
    "out/**",
    "build/**",
    "next-env.d.ts",
    "src/lib/api/generated/**",
  ]),
]);

export default eslintConfig;
