interface UserAvatarProps {
  initials: string;
  /** Nom complet : des initiales seules ne se devinent pas. */
  name: string;
  /** Un collaborateur desactive s'efface, sans disparaitre. */
  attenue?: boolean;
}

/** Pastille d'initiales identifiant un collaborateur. */
export function UserAvatar({ initials, name, attenue = false }: UserAvatarProps) {
  return (
    <span
      title={name}
      className={[
        "flex size-7 shrink-0 items-center justify-center rounded-full bg-slate-200 text-xs font-medium text-slate-700",
        attenue ? "opacity-50" : "",
      ].join(" ")}
    >
      {initials}
    </span>
  );
}
