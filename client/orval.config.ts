import { defineConfig } from "orval";

/**
 * Le client est genere depuis l'OpenAPI de FastAPI : aucun type d'API n'est
 * ecrit a la main.
 *
 * Aucune `baseUrl` n'est configuree : les chemins de l'OpenAPI contiennent deja
 * `/api/v1`, et le BFF expose exactement les memes. Les requetes relatives
 * atteignent donc les Route Handlers, qui relaient vers FastAPI en injectant le
 * jeton Entra. Le navigateur ne parle jamais directement a l'API.
 */
export default defineConfig({
  timesheet: {
    input: { target: "./openapi.json" },
    output: {
      mode: "tags-split",
      target: "./src/lib/api/generated/timesheet.ts",
      schemas: "./src/lib/api/generated/model",
      client: "react-query",
      override: {
        mutator: {
          path: "./src/lib/api/fetcher.ts",
          name: "bffFetcher",
        },
      },
    },
  },
});
