/**
 * The frame every screen of the application is read in.
 *
 * It only makes sense once someone is signed in: the sign-in screen lives
 * outside this group, and is drawn on a bare page. What the frame holds
 * depends on who is there, which only the client knows — hence `AppFrame`.
 */
import { AppFrame } from "@/components/organisms/AppFrame";

export default function AppLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return <AppFrame>{children}</AppFrame>;
}
