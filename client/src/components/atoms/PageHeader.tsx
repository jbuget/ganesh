interface PageHeaderProps {
  titre: string;
  soustitre: string;
  /** Actions portant sur l'ecran entier, alignees a droite. */
  actions?: React.ReactNode;
}

/**
 * En-tete commun a toutes les vues.
 *
 * Titre et sous-titre a gauche, actions generales a droite, sur toute la
 * largeur : les boutons se trouvent au meme endroit d'un ecran a l'autre, meme
 * quand le contenu en dessous est plus etroit.
 */
export function PageHeader({ titre, soustitre, actions }: PageHeaderProps) {
  return (
    <header className="mb-6 flex items-start justify-between gap-4">
      <div className="min-w-0">
        <h1 className="text-lg font-semibold">{titre}</h1>
        <p className="text-sm text-slate-500">{soustitre}</p>
      </div>

      {actions && <div className="flex shrink-0 items-center gap-3">{actions}</div>}
    </header>
  );
}
