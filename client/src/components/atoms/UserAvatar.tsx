interface UserAvatarProps {
  initiales: string;
  /** Nom complet : des initiales seules ne se devinent pas. */
  nom: string;
  /** Un collaborateur desactive s'efface, sans disparaitre. */
  attenue?: boolean;
}

/** Pastille d'initiales identifiant un collaborateur. */
export function UserAvatar({ initiales, nom, attenue = false }: UserAvatarProps) {
  return (
    <span
      title={nom}
      className={[
        "flex size-7 shrink-0 items-center justify-center rounded-full bg-slate-200 text-xs font-medium text-slate-700",
        attenue ? "opacity-50" : "",
      ].join(" ")}
    >
      {initiales}
    </span>
  );
}
