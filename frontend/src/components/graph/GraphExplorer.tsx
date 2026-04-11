"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAppStore, useHasHydrated } from "@/stores/appStore";
import { useJobGraph, useJobStatus, useGeneratePersonas } from "@/hooks/useApi";
import GraphCanvas from "./GraphCanvas";
import GraphControls from "./GraphControls";

export default function GraphExplorer() {
  const router = useRouter();
  const hasHydrated = useHasHydrated();
  const { jobId, setStep, setGraphData, jobStatus, setJobStatus, numUserPersonas, numAdversarialPersonas } = useAppStore();
  const { data: graphData, isLoading: isLoadingGraph } = useJobGraph(jobId);
  const { data: statusData } = useJobStatus(jobId);
  const generatePersonas = useGeneratePersonas();

  // Sync polled status into store
  useEffect(() => {
    if (statusData?.status && statusData.status !== jobStatus) {
      setJobStatus(statusData.status);
    }
  }, [statusData, jobStatus, setJobStatus]);

  useEffect(() => {
    setStep(3);
  }, [setStep]);

  useEffect(() => {
    if (!hasHydrated) return;
    if (!jobId) router.replace("/upload");
  }, [hasHydrated, jobId, router]);

  useEffect(() => {
    if (graphData) {
      setGraphData(graphData);
    }
  }, [graphData, setGraphData]);

  const handleGeneratePersonas = async () => {
    if (!jobId) return;
    try {
      await generatePersonas.mutateAsync({ jobId, numUser: numUserPersonas, numAdv: numAdversarialPersonas });
    } catch (error) {
      console.error("Failed to generate personas", error);
      alert("Failed to start persona generation. Check that the graph is ready.");
    }
  };

  if (!jobId) return null;

  return (
    <div className="w-full h-[calc(100vh-6rem)] relative">
      <GraphControls
        onGeneratePersonas={handleGeneratePersonas}
        isGenerating={generatePersonas.isPending || jobStatus === "persona_generating"}
      />

      {isLoadingGraph ? (
        <div className="flex flex-col items-center justify-center h-full gap-4">
          <div className="w-12 h-12 rounded-full border-2 border-[#00F0FF]/30 border-t-[#00F0FF] animate-spin" />
          <p className="text-gray-400 text-sm">Loading knowledge graph…</p>
        </div>
      ) : (
        <GraphCanvas graphData={graphData} />
      )}
    </div>
  );
}
