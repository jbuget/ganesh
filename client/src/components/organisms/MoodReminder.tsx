"use client";

import { MoodPicker } from "@/components/atoms/MoodPicker";
import { STRONG_RULE } from "@/lib/table-frame";
import { useMoodReminder } from "@/lib/use-mood-reminder";

/**
 * The day's mood, asked for once the afternoon is over.
 *
 * The first thing in the application that convokes anybody, and a deliberate
 * exception: the window closes on the next working day, and a question nobody
 * is ever asked is a question answered by whoever already thought of it. A
 * morale made of the diligent measures diligence.
 *
 * It is the relance that lets « Moral de l'équipe » go on reading and never
 * writing. The question comes to the reader, wherever they are, rather than
 * opening a second door on the one screen that shows what everybody else
 * answered — which is what the whole thing was built to avoid.
 *
 * Three things keep it from becoming a nag: it is turned down in one click
 * and believed until tomorrow, it never shows on the two screens that already
 * ask, and it asks for today alone. Catching up on yesterday is done from the
 * home screen, at one's own pace.
 *
 * Bottom right and under the panels rather than over them: it arrives on its
 * own, and what one opened oneself comes first. The frame is the strong rule
 * the application closes an object at — it asks something of the reader, and
 * a question drawn like a notice gets read like a notice.
 *
 * It rises into place rather than appearing outright: a panel that is simply
 * there was always there as far as the eye is concerned, and the eye does not
 * go back to it. The movement is what makes the question a question.
 *
 * Slowly, and after the reader has been left alone a moment — `useSettledIn`
 * holds it back. A panel that shoots up the instant one lands somewhere is an
 * interruption; one that rises gently once the page has been read is an offer.
 *
 * It rises once, and not again at every screen. Nothing here arranges that:
 * the reminder lives in the frame, so moving from « Projets » to « Kanban »
 * leaves the same element in place and the animation has nothing to replay.
 * Only a real disappearance and return plays it again — through « Moral », say,
 * which the reminder stays away from — and there it is right, since the panel
 * really did come back.
 *
 * Whoever asked for less movement gets none: the question is worth drawing the
 * eye, never worth making somebody unwell.
 */
export function MoodReminder() {
  const reminder = useMoodReminder();

  if (!reminder.show) return null;

  return (
    // Announced rather than slipped in: it appears without anybody asking, and
    // a reader who does not watch that corner would never know it was there.
    <section
      role="status"
      aria-label="Mon moral"
      className={`fixed bottom-4 right-4 z-30 w-72 max-w-[calc(100vw-2rem)] animate-in rounded-xl border bg-white p-3 shadow-lg duration-700 ease-out fade-in-0 slide-in-from-bottom-8 motion-reduce:animate-none ${STRONG_RULE}`}
    >
      <header className="mb-2">
        <h2 className="text-sm font-medium text-slate-700">
          Comment s&apos;est passée votre journée&nbsp;?
        </h2>
        <p className="text-xs text-slate-400">
          Toute l&apos;équipe lit le résultat, et personne ne répond à votre place.
        </p>
      </header>

      {/* Never anything but null: the question is only asked on a day nobody
          has answered for. Changing one's mind happens on the home screen,
          where the answer already given is there to be taken back. */}
      <MoodPicker value={null} onPick={reminder.post} disabled={reminder.saving} />

      {/* One way out, and it says what it does. « Pas aujourd'hui » is a
          refusal that expires; a cross would only say « later », and later is
          what one never comes back to. */}
      <button
        type="button"
        onClick={reminder.dismiss}
        className="mt-2 cursor-pointer text-xs text-slate-400 underline-offset-2 hover:text-slate-600 hover:underline"
      >
        Pas aujourd&apos;hui
      </button>
    </section>
  );
}
