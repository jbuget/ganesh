import { defineConfig } from "orval";

/**
 * The client is generated from FastAPI's OpenAPI: no API type is written by
 * hand.
 *
 * No `baseUrl` is configured: the OpenAPI paths already carry `/api/v1`, and
 * the BFF exposes exactly the same ones. Relative requests therefore reach the
 * Route Handlers, which relay to FastAPI, injecting the Entra token. The
 * browser never talks to the API directly.
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
