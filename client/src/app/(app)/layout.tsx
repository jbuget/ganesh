/**
 * The frame every screen of the application is read in.
 *
 * It holds the sidebar, which only makes sense once someone is signed in:
 * the sign-in screen lives outside this group, and is drawn on a bare page.
 */
import { AppSidebar } from "@/components/organisms/AppSidebar";
import { CommandPalette } from "@/components/organisms/CommandPalette";

export default function AppLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <div className="flex min-h-screen">
      <AppSidebar />
      <div className="min-w-0 flex-1">{children}</div>
      {/* In the frame rather than on a screen: it is reached from every one of
          them, and its shortcut listens to the whole window. */}
      <CommandPalette />
    </div>
  );
}
