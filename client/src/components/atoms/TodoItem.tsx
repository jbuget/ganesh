import type { LucideIcon } from "lucide-react";

interface TodoItemProps {
  icon: LucideIcon;
  /** The sentence, and whatever it names inside it. */
  children: React.ReactNode;
  /** What closes the item, aligned right. */
  action?: React.ReactNode;
}

/**
 * One thing left to do, on its line.
 *
 * Amber on the mark alone, the sentence in ordinary slate: this is the tone
 * the application keeps for what one must know before writing, and a list of
 * reminders whose every line shouts is a list nobody reads. The colour marks
 * where to look; the words say what to do.
 */
export function TodoItem({ icon: Icon, children, action }: TodoItemProps) {
  return (
    <li className="flex items-center gap-2 py-1.5 text-sm text-slate-700">
      <Icon className="size-4 shrink-0 text-amber-500" aria-hidden />
      <span className="min-w-0 flex-1">{children}</span>
      {action && <span className="shrink-0">{action}</span>}
    </li>
  );
}
