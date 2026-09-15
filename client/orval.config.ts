import { defineConfig } from "orval";

/**
 * Le client est genere depuis l'OpenAPI de FastAPI : aucun type d'API n'est
 * ecrit a la main.
 *
 * La baseUrl pointe vers le BFF (`/api/v1`), pas vers FastAPI : le navigateur
 * ne parle jamais directement a l'API, les Route Handlers relaient en injectant
 * le jeton Entra.
 */
export default defineConfig({
  timesheet: {
    input: { target: "./openapi.json" },
    output: {
      mode: "tags-split",
      target: "./src/lib/api/generated/timesheet.ts",
      schemas: "./src/lib/api/generated/model",
      client: "react-query",
      baseUrl: "/api/v1",
      override: {
        mutator: {
          path: "./src/lib/api/fetcher.ts",
          name: "bffFetcher",
        },
      },
    },
  },
});
