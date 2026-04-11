"use client";

import { useQuery, useMutation } from "@tanstack/react-query";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001/api";

export function useUploadDocument() {
  return useMutation({
    mutationFn: async ({ file, prompt }: { file: File; prompt: string }) => {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("simulation_prompt", prompt);
      const res = await fetch(`${API_BASE}/upload`, { method: "POST", body: formData });
      if (!res.ok) throw new Error(await res.text());
      return res.json();
    },
  });
}

export function useJobStatus(jobId: string | null) {
  return useQuery({
    queryKey: ["job", jobId],
    queryFn: async () => {
      const res = await fetch(`${API_BASE}/job/${jobId}/status`);
      if (!res.ok) throw new Error("Failed to fetch status");
      return res.json();
    },
    enabled: !!jobId,
    refetchInterval: (query) => {
      const data = query.state.data;
      // Stop polling once the pipeline reaches a stable terminal state
      if (data?.status === "done" || data?.status === "error" || data?.status === "graph_ready") return false;
      return 2000;
    },
  });
}

export function useJobGraph(jobId: string | null) {
  return useQuery({
    queryKey: ["graph", jobId],
    queryFn: async () => {
      const res = await fetch(`${API_BASE}/job/${jobId}/graph`);
      if (!res.ok) throw new Error("Graph not ready");
      return res.json();
    },
    enabled: !!jobId,
    retry: 5,
    retryDelay: 2000,
    staleTime: Infinity,
    refetchOnWindowFocus: false,
  });
}

export function useGeneratePersonas() {
  return useMutation({
    mutationFn: async ({
      jobId,
      numUser = 10,
      numAdv = 10,
    }: {
      jobId: string;
      numUser?: number;
      numAdv?: number;
    }) => {
      const res = await fetch(`${API_BASE}/job/${jobId}/generate-personas`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ num_user_personas: numUser, num_adversarial_personas: numAdv }),
      });
      if (!res.ok) throw new Error(await res.text());
      return res.json();
    },
  });
}

export function useJobPersonas(jobId: string | null) {
  return useQuery({
    queryKey: ["personas", jobId],
    queryFn: async () => {
      const res = await fetch(`${API_BASE}/job/${jobId}/personas`);
      if (!res.ok) throw new Error("Failed to fetch personas");
      return res.json();
    },
    enabled: !!jobId,
    refetchInterval: (query) => {
      const data = query.state.data;
      return data?.total > 0 ? false : 4000;
    },
  });
}

export function useJobCoverage(jobId: string | null) {
  return useQuery({
    queryKey: ["coverage", jobId],
    queryFn: async () => {
      const res = await fetch(`${API_BASE}/job/${jobId}/coverage`);
      if (!res.ok) throw new Error("Failed to fetch coverage");
      return res.json();
    },
    enabled: !!jobId,
  });
}

export function useGenerateMissing() {
  return useMutation({
    mutationFn: async ({ jobId, taxonomyId }: { jobId: string; taxonomyId: string }) => {
      const res = await fetch(`${API_BASE}/job/${jobId}/generate-missing`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ taxonomy_id: taxonomyId }),
      });
      if (!res.ok) throw new Error(await res.text());
      return res.json();
    },
  });
}

export function getExportUrl(jobId: string, format: "json" | "csv", team?: string) {
  const params = new URLSearchParams({ format });
  if (team) params.set("team", team);
  return `${API_BASE}/job/${jobId}/export?${params}`;
}
