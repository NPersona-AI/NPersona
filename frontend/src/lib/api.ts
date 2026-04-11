export const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001/api";

export async function uploadDocument(file: File, prompt: string): Promise<{ job_id: string }> {
  const form = new FormData();
  form.append("file", file);
  form.append("simulation_prompt", prompt);
  const res = await fetch(`${API}/upload`, { method: "POST", body: form });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getJobStatus(jobId: string) {
  const res = await fetch(`${API}/job/${jobId}/status`);
  if (!res.ok) throw new Error("Failed to fetch status");
  return res.json();
}

export async function getGraph(jobId: string) {
  const res = await fetch(`${API}/job/${jobId}/graph`);
  if (!res.ok) throw new Error("Graph not ready");
  return res.json();
}

export async function generatePersonas(jobId: string, numUser: number, numAdv: number) {
  const res = await fetch(`${API}/job/${jobId}/generate-personas`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ num_user_personas: numUser, num_adversarial_personas: numAdv }),
  });
  if (!res.ok) throw new Error("Failed to start generation");
  return res.json();
}

export async function getPersonas(jobId: string) {
  const res = await fetch(`${API}/job/${jobId}/personas`);
  if (!res.ok) throw new Error("Failed to fetch personas");
  return res.json();
}

export async function getCoverage(jobId: string) {
  const res = await fetch(`${API}/job/${jobId}/coverage`);
  if (!res.ok) throw new Error("Failed to fetch coverage");
  return res.json();
}
