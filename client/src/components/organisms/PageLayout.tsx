"use client";

interface PageLayoutProps {
  /** L'en-tete de l'ecran, qui ne defile pas. */
  entete: React.ReactNode;
  /**
   * Pour un ecran qui organise lui-meme son defilement — le kanban et ses
   * colonnes — au lieu de le laisser a la page entiere.
   */
  defilementInterne?: boolean;
  children: React.ReactNode;
}

/**
 * Le squelette commun a toutes les vues : un en-tete fixe, un contenu qui
 * defile dessous.
 *
 * L'ecran tient dans la fenetre et c'est le contenu seul qui bouge : le titre
 * et les actions restent sous les yeux, quelle que soit la longueur de la
 * liste. C'est aussi ce qui permet aux en-tetes de tableau de se figer, faute
 * de quoi ils se caleraient sur la fenetre et passeraient sous celui de la
 * page.
 */
export function PageLayout({
  entete,
  defilementInterne = false,
  children,
}: PageLayoutProps) {
  return (
    <main className="flex h-screen flex-col">
      <div className="shrink-0 px-6 pt-6">{entete}</div>

      <div
        className={[
          "min-h-0 flex-1 px-6 pb-6",
          defilementInterne ? "overflow-hidden" : "overflow-y-auto",
        ].join(" ")}
      >
        {children}
      </div>
    </main>
  );
}
