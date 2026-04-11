import JobDashboard from "@/components/JobDashboard";

interface Props {
  params: Promise<{ jobId: string }>;
}

export default async function JobPage({ params }: Props) {
  const { jobId } = await params;
  return <JobDashboard jobId={jobId} />;
}
