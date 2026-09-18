import { ProjectDetailPage } from "@/components/organisms/ProjectDetailPage";

export default async function ProjectRoute({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return <ProjectDetailPage projectId={Number(id)} />;
}
