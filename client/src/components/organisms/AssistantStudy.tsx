"use client";

import { AssistantIndicatorsBand } from "@/components/atoms/AssistantIndicatorsBand";
import { AssistantStudyFilters } from "@/components/molecules/AssistantStudyFilters";
import { UnansweredQuestionPanel } from "@/components/molecules/UnansweredQuestionPanel";
import { AssistantConversationPanel } from "@/components/organisms/AssistantConversationPanel";
import { AssistantConversationsTable } from "@/components/organisms/AssistantConversationsTable";
import { UnansweredQuestionsTable } from "@/components/organisms/UnansweredQuestionsTable";
import { Button } from "@/components/ui/button";
import { hasStudyFilter } from "@/lib/assistant-study";
import { useOpenedConversation } from "@/lib/opened-conversation";
import { useAssistantStudy } from "@/lib/use-assistant-study";
import { useStudiedConversation } from "@/lib/use-studied-conversation";

/**
 * The assistant, studied: everybody's questions, and what came back.
 *
 * Kept to improve it, and read here for that alone — which answers help, and
 * why the others went wrong. The figures come first, the conversations under
 * them, and one conversation opens beside the list with what every tool read.
 * The questions that came back with no answer follow, apart: they hold no
 * answer to judge or annotate, only a reason and what was read before.
 *
 * Nobody is anonymised: the team trusts itself, and a question is understood
 * by knowing who asked it and from where.
 */
export function AssistantStudy() {
  const study = useAssistantStudy();
  const panel = useOpenedConversation();
  const opened = useStudiedConversation(panel.openedConversation);

  return (
    <div className="max-w-[1050px] space-y-6">
      <AssistantStudyFilters
        filters={study.filters}
        teammates={study.teammates}
        onChange={study.change}
        onClear={study.clear}
        exportUrl={study.exportUrl}
      />

      {study.indicators && <AssistantIndicatorsBand indicators={study.indicators} />}

      <section className="space-y-2">
        <h2 className="text-sm font-semibold">Conversations</h2>

        {study.isLoading && <p className="text-sm text-slate-500">Chargement…</p>}

        {!study.isLoading && study.conversations.length === 0 && (
          <p className="py-8 text-center text-sm text-slate-500">
            {hasStudyFilter(study.filters)
              ? "Aucune conversation ne répond aux filtres."
              : "Personne n'a encore rien demandé à l'assistant."}
          </p>
        )}

        {study.conversations.length > 0 && (
          <>
            <AssistantConversationsTable
              conversations={study.conversations}
              askerName={study.askerName}
              onOpen={panel.open}
            />

            <div className="flex items-center justify-between text-sm text-slate-500">
              <span>
                {study.firstShown}–{study.lastShown} sur {study.total}
              </span>
              <span className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={!study.hasPrevious}
                  onClick={study.previous}
                  className="cursor-pointer"
                >
                  Précédentes
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={!study.hasNext}
                  onClick={study.next}
                  className="cursor-pointer"
                >
                  Suivantes
                </Button>
              </span>
            </div>
          </>
        )}
      </section>

      {study.unanswered.length > 0 && (
        <section className="space-y-2">
          <h2 className="text-sm font-semibold">Questions sans réponse</h2>
          <p className="text-xs text-slate-500">
            Ce que l&apos;assistant a dit « indisponible ». Les{" "}
            {study.unanswered.length < study.unansweredTotal
              ? `${study.unanswered.length} plus récentes sur ${study.unansweredTotal}`
              : "plus récentes d'abord"}
            .
          </p>
          <UnansweredQuestionsTable
            questions={study.unanswered}
            askerName={study.askerName}
            onOpen={study.openUnanswered}
          />
        </section>
      )}

      {study.openedUnanswered && (
        <UnansweredQuestionPanel
          question={study.openedUnanswered}
          askerName={study.askerName(study.openedUnanswered.asker_id)}
          projectLabel={study.projectLabel}
          onClose={study.closeUnanswered}
        />
      )}

      {panel.openedConversation && (
        <AssistantConversationPanel
          conversation={opened.conversation}
          askerName={study.askerName}
          projectLabel={study.projectLabel}
          onAnnotate={opened.annotate}
          onClose={panel.close}
        />
      )}
    </div>
  );
}
