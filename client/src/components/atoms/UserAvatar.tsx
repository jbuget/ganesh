interface UserAvatarProps {
  initials: string;
  /** Full name: initials alone cannot be guessed. */
  name: string;
  /** A deactivated teammate fades, without disappearing. */
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
