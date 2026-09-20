"use client";

import { CopyableSnippet } from "@/components/atoms/CopyableSnippet";
import { scopeLabel } from "@/lib/api-keys";
import { MCP_CLIENTS, MCP_SCOPES, MCP_TOOLS, MCP_URL } from "@/lib/mcp";

/**
 * How a terminal client reaches Ganesh.
 *
 * Beside the keys rather than in a page of its own: a key is the whole of
 * what stands between a terminal and the server, and the two questions — « où
 * est ma clé » and « où est-ce que je la colle » — are asked in the same
 * minute. A screen that separated them would send the reader back and forth.
 *
 * Read-only, and stays so: what a key opens is decided in the « API » tab,
 * which is where a manager mints one. Here there is nothing to click but
 * « Copier ».
 */
export function McpTab() {
  return (
    <div className="flex max-w-[860px] flex-col gap-8">
      <section className="flex flex-col gap-3">
        <h2 className="text-sm font-semibold text-slate-900">Ce que ça change</h2>
        <p className="text-sm text-slate-600">
          Ganesh répond à un client MCP à l&apos;adresse{" "}
          <code className="rounded bg-slate-100 px-1 py-0.5 font-mono text-xs text-slate-800">
            {MCP_URL}
          </code>
          . Une fois branché, votre terminal sait répondre à « où en est mon mois ? » ou
          « qu&apos;est-ce qui a bougé sur ce projet ? » sans quitter la ligne de
          commande — et sait y déclarer votre temps. La seule écriture possible est
          celle-là, et elle ne touche que votre mois : aucun outil n&apos;écrit dans
          celui d&apos;un collègue.
        </p>
      </section>

      <section className="flex flex-col gap-3">
        <h2 className="text-sm font-semibold text-slate-900">1. Obtenir une clé</h2>
        <p className="text-sm text-slate-600">
          Un manager vous crée une clé depuis l&apos;onglet « API », à votre nom,
          portant ces habilitations :
        </p>
        {/* A plain disc, not a drawn dot: a round mark is what carries a
            phase everywhere else in the application, and a list of
            permissions must not borrow its grammar. */}
        <ul className="list-inside list-disc text-sm text-slate-600">
          {MCP_SCOPES.map((scope) => (
            <li key={scope}>
              {scopeLabel(scope)}{" "}
              <code className="font-mono text-xs text-slate-500">{scope}</code>
            </li>
          ))}
        </ul>
        <p className="text-sm text-slate-600">
          La clé ne s&apos;affiche qu&apos;une fois, à sa création. Elle vous est propre
          : les outils répondent pour son porteur, jamais pour un collègue.
        </p>
        <p className="text-sm text-slate-600">
          « Moral de l&apos;équipe » se coche à part : aucune des deux cases « Tous » ne
          l&apos;ouvre. C&apos;est la seule habilitation dans ce cas, et ce n&apos;est
          pas un oubli — ce qu&apos;elle donne à lire a été confié à un écran interne,
          et y accéder depuis un terminal est une décision que quelqu&apos;un prend, sur
          une clé que toute l&apos;équipe peut relire.
        </p>
      </section>

      <section className="flex flex-col gap-4">
        <div className="flex flex-col gap-1">
          <h2 className="text-sm font-semibold text-slate-900">
            2. Brancher votre client
          </h2>
          <p className="text-sm text-slate-600">
            Remplacez <code className="font-mono text-xs">jns_…</code> par votre clé.
          </p>
        </div>

        {MCP_CLIENTS.map((client) => (
          <div
            key={client.id}
            className="flex flex-col gap-2 rounded-md border border-slate-200 bg-white p-4"
          >
            <div className="flex items-baseline justify-between gap-3">
              <h3 className="text-sm font-semibold text-slate-900">{client.name}</h3>
              <span className="text-xs text-slate-500">{client.where}</span>
            </div>

            <CopyableSnippet
              value={client.snippet}
              label={`Copier la configuration ${client.name}`}
            />

            {client.note && <p className="text-xs text-slate-500">{client.note}</p>}
          </div>
        ))}
      </section>

      <section className="flex flex-col gap-3">
        <h2 className="text-sm font-semibold text-slate-900">
          3. Ce que vous pouvez demander
        </h2>
        <ul className="flex flex-col gap-3">
          {MCP_TOOLS.map((tool) => (
            <li key={tool.name} className="flex flex-col gap-1">
              <div className="flex items-baseline gap-2">
                <code className="font-mono text-xs font-semibold text-slate-800">
                  {tool.name}
                </code>
                <span className="text-xs text-slate-500">{scopeLabel(tool.scope)}</span>
              </div>
              <p className="text-sm text-slate-600">{tool.answers}</p>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
