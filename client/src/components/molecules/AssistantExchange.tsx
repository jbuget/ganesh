import { AnswerVerdict } from "@/components/atoms/AnswerVerdict";
import { MarkdownView } from "@/components/atoms/MarkdownView";
import { NameLink } from "@/components/atoms/NameLink";
import type { Verdict } from "@/lib/api/generated/model";
import { remarkNames } from "@/lib/assistant";
import type { AssistantTurn } from "@/lib/use-assistant";

interface AssistantExchangeProps {
  turn: AssistantTurn;
  /** Where every project and person the answer may name leads. */
  names: Map<string, string>;
  onJudge: (exchangeId: number, verdict: Verdict) => void;
}

/**
 * One question, its answer, and where the answer was read.
 *
 * The projects consulted are links: an answer about a project somebody does
 * not know is only trusted once they can open it and check. So is every
 * project and person the answer names — the names are what a reader scans
 * an answer for, and they stand out from the prose around them.
 */
export function AssistantExchange({ turn, names, onJudge }: AssistantExchangeProps) {
  return (
    <li className="flex flex-col gap-2">
      <p className="self-end rounded bg-slate-100 px-3 py-2 text-sm whitespace-pre-wrap text-slate-900">
        {turn.question}
      </p>

      <MarkdownView
        body={turn.answer}
        plugins={[remarkNames(names)]}
        images={false}
        renderLink={(href, children) => <NameLink href={href}>{children}</NameLink>}
      />

      <div className="flex items-center justify-between gap-2 text-xs text-slate-500">
        {turn.consulted.length > 0 ? (
          <p>
            Lu dans{" "}
            {turn.consulted.map((project, index) => (
              <span key={project.id}>
                {index > 0 && ", "}
                <NameLink href={`/projects/${project.id}`}>{project.label}</NameLink>
              </span>
            ))}
          </p>
        ) : (
          <span />
        )}
        <AnswerVerdict
          verdict={turn.verdict}
          onJudge={(verdict) => onJudge(turn.id, verdict)}
        />
      </div>
    </li>
  );
}
