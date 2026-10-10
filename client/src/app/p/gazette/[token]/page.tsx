import type { Metadata } from "next";

import { SharedGazettePage } from "@/components/organisms/SharedGazettePage";

/**
 * What the team sent a link to: a narrative, read by somebody who has not
 * signed in. Kept out of search engines, and the address — which carries the
 * token — kept from travelling to whatever the page loads.
 */
export const metadata: Metadata = {
  title: "La Gazette — WAAT",
  robots: { index: false, follow: false },
  referrer: "no-referrer",
};

export default async function SharedGazette({
  params,
}: Readonly<{ params: Promise<{ token: string }> }>) {
  const { token } = await params;
  return <SharedGazettePage token={token} />;
}
