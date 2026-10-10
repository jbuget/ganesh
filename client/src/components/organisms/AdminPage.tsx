"use client";

import { PageHeader } from "@/components/atoms/PageHeader";
import { AdminPlatform } from "@/components/organisms/AdminPlatform";
import { AssistantStudy } from "@/components/organisms/AssistantStudy";
import { PageLayout } from "@/components/organisms/PageLayout";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { type AdminView, useAdminView } from "@/lib/use-admin-view";

/**
 * The administration: the platform, and the assistant.
 *
 * Administrators only, and the whole screen is the permission: there is no
 * reading here a manager may have, which is why the sidebar hides it rather
 * than showing it and refusing.
 *
 * Two tabs for two questions. « Plateforme » is read and never steered: how
 * Ganesh is wired. « Assistant IA » reads everybody's questions to the
 * assistant, to study it and improve it — which is why it sits here, behind
 * the one door above the manager's, rather than anywhere the team goes.
 */
export function AdminPage() {
  const { view, show } = useAdminView();

  return (
    <PageLayout
      header={
        <PageHeader
          title="Administration"
          subtitle="Comment Ganesh est branché, et ce que l'assistant répond."
        />
      }
    >
      <Tabs value={view} onValueChange={(next) => show(next as AdminView)}>
        <TabsList>
          <TabsTrigger value="plateforme" className="cursor-pointer">
            Plateforme
          </TabsTrigger>
          <TabsTrigger value="assistant" className="cursor-pointer">
            Assistant IA
          </TabsTrigger>
        </TabsList>

        <TabsContent value="plateforme" className="mt-4">
          <AdminPlatform />
        </TabsContent>

        <TabsContent value="assistant" className="mt-4">
          <AssistantStudy />
        </TabsContent>
      </Tabs>
    </PageLayout>
  );
}
