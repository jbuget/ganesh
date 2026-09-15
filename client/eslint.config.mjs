import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";
import boundaries from "eslint-plugin-boundaries";

const eslintConfig = defineConfig([
  ...nextVitals,
  ...nextTs,

  // --- Atomic Design : les regles de composition deviennent des erreurs -------
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
            // Les paquets npm restent libres.
            { allow: { to: { module: { origin: "external" } } } },
            // Un fichier de test peut importer le composant qu'il verifie.
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
            // Un atom n'importe jamais un autre composant local.
            {
              from: { element: { type: "atoms" } },
              allow: { to: { element: { types: { anyOf: ["ui", "lib"] } } } },
            },
            // Une molecule n'importe que des atoms.
            {
              from: { element: { type: "molecules" } },
              allow: {
                to: { element: { types: { anyOf: ["atoms", "ui", "lib"] } } },
              },
            },
            // Un organism peut importer des atoms et des molecules.
            {
              from: { element: { type: "organisms" } },
              allow: {
                to: {
                  element: {
                    types: { anyOf: ["atoms", "molecules", "ui", "lib"] },
                  },
                },
              },
            },
            // Les pages n'importent que des organisms.
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
