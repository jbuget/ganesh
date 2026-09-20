/**
 * What a terminal client needs to reach Ganesh, and what it will find there.
 *
 * Held here rather than inside the tab so it can be read by a test: a
 * configuration snippet somebody pastes into their shell is exactly the kind
 * of text that rots quietly — the address moves, a flag is renamed, and the
 * screen goes on saying the old thing with perfect confidence.
 *
 * The address is the production one, written out. It is the only one a
 * terminal connects to: nobody points Claude Code at a colleague's laptop,
 * and an address computed from wherever the browser happens to be would hand
 * a `localhost` snippet to whoever opened the screen from a dev server.
 */

import type { ApiKeyScope } from "@/lib/api/generated/model";

/** The address that answers. `/mcp` redirects to it, keeping method and body. */
export const MCP_URL = "https://api.ganesh.waat.tools/mcp/";

/** The name a client knows the server by, in every snippet below. */
export const MCP_SERVER_NAME = "ganesh";

/**
 * The scopes the tools open, and therefore what the key must carry.
 *
 * Typed as the API's own scopes rather than as strings: the two tabs name the
 * same things, and a scope renamed on one side must not leave the other
 * quietly asking for a member nobody honours any more.
 *
 * `moods:read` is the one a reader has to tick on purpose: no « Tous » covers
 * it, on the server as on the form. Somebody granting « Tous (lecture) » and
 * expecting `team_mood` would be handed a key that refuses it.
 */
export const MCP_SCOPES: ApiKeyScope[] = [
  "projects:read",
  "entries:read",
  "entries:write",
  "audit:read",
  "roadmap:read",
  "moods:read",
];

export interface McpClientSetup {
  id: string;
  /** The client's own name, spelled as its makers spell it. */
  name: string;
  /** Where the snippet goes: a shell, or a file at this path. */
  where: string;
  language: "shell" | "toml" | "json";
  snippet: string;
  /** What the snippet does not say on its own. */
  note?: string;
}

/**
 * Where the key goes, one client at a time.
 *
 * `jns_…` is left standing in the snippets on purpose: a reader pasting one
 * has to go and fetch their own key, and a placeholder that looked like a key
 * would be pasted as is.
 */
export const MCP_CLIENTS: McpClientSetup[] = [
  {
    id: "claude-code",
    name: "Claude Code",
    where: "Ligne de commande",
    language: "shell",
    snippet: [
      `claude mcp add --transport http ${MCP_SERVER_NAME} ${MCP_URL} \\`,
      `  --header "Authorization: Bearer jns_…"`,
    ].join("\n"),
    note: "À lancer depuis n'importe quel dossier. Ajoutez --scope user pour que le serveur vous suive sur tous vos projets, plutôt que sur le dossier courant.",
  },
  {
    id: "codex",
    name: "Codex",
    where: "~/.codex/config.toml",
    language: "toml",
    snippet: [
      `[mcp_servers.${MCP_SERVER_NAME}]`,
      `url = "${MCP_URL}"`,
      `bearer_token_env_var = "GANESH_API_KEY"`,
    ].join("\n"),
    note: "Codex lit la clé dans l'environnement : exportez GANESH_API_KEY=jns_… avant de le lancer. La clé ne reste pas dans le fichier.",
  },
  {
    id: "gemini-cli",
    name: "Gemini CLI",
    where: "~/.gemini/settings.json",
    language: "json",
    snippet: [
      `{`,
      `  "mcpServers": {`,
      `    "${MCP_SERVER_NAME}": {`,
      `      "httpUrl": "${MCP_URL}",`,
      `      "headers": { "Authorization": "Bearer jns_…" }`,
      `    }`,
      `  }`,
      `}`,
    ].join("\n"),
    note: "httpUrl, et non url : c'est ce qui dit à Gemini CLI de parler en HTTP continu plutôt que de lancer un processus.",
  },
];

export interface McpTool {
  name: string;
  /** What it answers, in the words somebody would ask it. */
  answers: string;
  /** The scope it opens, as the table of keys names it. */
  scope: ApiKeyScope;
}

/**
 * The questions the server knows how to answer.
 *
 * Read here as they are written in the server's own docstrings: a tool is a
 * question somebody asks, so what the screen shows is the question.
 *
 * A tool added on the server and forgotten here is a tool nobody knows to ask
 * for, which is why `test_the_screen_lists_every_tool_the_server_offers` reads
 * this list from the other side.
 */
export const MCP_TOOLS: McpTool[] = [
  {
    name: "find_project",
    answers:
      "Trouve un projet du référentiel à partir de son nom, même approximatif, et rend son identifiant, sa nature et sa phase.",
    scope: "projects:read",
  },
  {
    name: "my_month",
    answers:
      "Dit où en est votre mois : ce qui est déclaré, ce qui manque encore, et si le mois est validé. Toujours le vôtre, jamais celui d'un collègue.",
    scope: "entries:read",
  },
  {
    name: "declare_time",
    answers:
      "Déclare une demi-journée ou une journée sur un projet, dans votre mois et dans aucun autre. Un week-end, un jour férié ou un mois validé sont refusés en toutes lettres.",
    scope: "entries:write",
  },
  {
    name: "what_changed",
    answers:
      "Dit ce qui a bougé sur un projet depuis une date : la phase, le temps déclaré, les mises à jour postées. Quinze jours en arrière par défaut.",
    scope: "audit:read",
  },
  {
    name: "portfolio_status",
    answers:
      "Dit où en est le portefeuille : ce qui est en retard et de combien, ce qui a été mis en service, et les projets que la projection n'a pas pu placer.",
    scope: "roadmap:read",
  },
  {
    name: "team_mood",
    answers:
      "Dit le moral de l'équipe sur la quinzaine, en chiffres d'ensemble : aucun nom, et une journée à moins de trois réponses est annoncée plutôt que moyennée.",
    scope: "moods:read",
  },
];
