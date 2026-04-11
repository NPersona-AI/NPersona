"use client";

import { useEffect, useRef } from "react";
import { useAppStore, useHasHydrated } from "@/stores/appStore";
import { useJobStatus } from "@/hooks/useApi";
import { useRouter } from "next/navigation";
import { GitBranch, AlertTriangle, RefreshCw, ArrowRight } from "lucide-react";

const STAGES = [
  { key: "parsing",       label: "Parsing document" },
  { key: "graph_building", label: "Extracting entities via LLM" },
  { key: "graph_ready",   label: "Writing to Neo4j" },
];

const STAGE_ORDER = ["parsing", "graph_building", "graph_ready", "persona_generating", "done"];

function stageIndex(s: string | null) {
  return s ? STAGE_ORDER.indexOf(s) : -1;
}

const LOG_STYLES: Record<string, string> = {
  stage:   "text-yellow-300 font-semibold",
  node:    "text-cyan-400",
  edge:    "text-purple-400",
  persona: "text-pink-400",
  success: "text-green-400",
  error:   "text-red-400",
  info:    "text-gray-400",
};

export default function GraphBuilder() {
  const router = useRouter();
  const { jobId, jobStatus, logs, setStep, setJobStatus, resetJob } = useAppStore();
  const hasHydrated = useHasHydrated();
  const errorTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const logEndRef = useRef<HTMLDivElement | null>(null);

  const { data: statusData } = useJobStatus(jobId);

  useEffect(() => {
    if (statusData?.status && statusData.status !== jobStatus) {
      setJobStatus(statusData.status);
    }
  }, [statusData, jobStatus, setJobStatus]);

  useEffect(() => { setStep(2); }, [setStep]);

  useEffect(() => {
    // Wait for localStorage to hydrate before deciding jobId is truly missing
    if (!hasHydrated) return;
    if (!jobId) { console.error("[GraphBuilder] no jobId after hydration → /upload"); router.replace("/upload"); }
  }, [hasHydrated, jobId, router]);

  // Auto-scroll log to bottom
  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs]);

  const currentStatus = statusData?.status || jobStatus;
  const isError = currentStatus === "error";
  const isDone = currentStatus === "graph_ready" || currentStatus === "persona_generating" || currentStatus === "done";
  const curIdx = stageIndex(currentStatus);

  useEffect(() => {
    if (isError && !errorTimerRef.current) {
      console.error("[GraphBuilder] isError → scheduling /upload in 4s, status:", currentStatus);
      errorTimerRef.current = setTimeout(() => {
        resetJob();
        router.replace("/upload");
      }, 4000);
    }
    return () => {
      if (errorTimerRef.current) { clearTimeout(errorTimerRef.current); errorTimerRef.current = null; }
    };
  }, [currentStatus, isError, router, resetJob]);

  // Stats derived from logs
  const nodeCount = logs.filter(l => l.type === "node").length;
  const edgeCount = logs.filter(l => l.type === "edge").length;
  const personaCount = logs.filter(l => l.type === "persona").length;

  return (
    <div className="w-full h-[calc(100vh-6rem)] flex flex-col items-center justify-start pt-8 px-4 overflow-hidden">

      {/* Header */}
      <div className="flex items-center gap-3 mb-6 w-full max-w-3xl">
        <div className={`p-2 rounded-xl border ${isError ? "bg-red-900/20 border-red-700/30" : "bg-[#00F0FF]/10 border-[#00F0FF]/20"}`}>
          {isError ? <AlertTriangle size={22} className="text-red-400" /> : <GitBranch size={22} className="text-cyan-400" />}
        </div>
        <div className="flex-1">
          <h2 className="text-lg font-bold text-white">
            {isError ? "Pipeline Failed" : isDone ? "Knowledge Graph Ready" : "Building Knowledge Graph"}
          </h2>
          <p className="text-xs text-gray-500 font-mono">job: {jobId}</p>
        </div>
        {isDone && (
          <button
            onClick={() => router.push("/graph-explorer")}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-gradient-to-r from-cyan-500/80 to-pink-500/80 hover:from-cyan-500 hover:to-pink-500 text-white text-sm font-bold transition-all"
          >
            View Graph <ArrowRight size={14} />
          </button>
        )}
        {isError && (
          <button
            onClick={() => { resetJob(); router.push("/upload"); }}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-red-900/40 hover:bg-red-900/60 border border-red-700/40 text-red-300 text-sm font-bold transition-all"
          >
            <RefreshCw size={14} /> Start Over
          </button>
        )}
      </div>

      {/* Stage bar */}
      <div className="flex items-center gap-2 mb-6 w-full max-w-3xl">
        {STAGES.map((stage, i) => {
          const stageIdx = stageIndex(stage.key);
          const done = curIdx > stageIdx || isDone;
          const active = !done && curIdx === stageIdx - 1 && !isError;
          const failed = isError && !done;
          return (
            <div key={stage.key} className="flex items-center gap-2 flex-1">
              <div className={`flex items-center gap-2 rounded-xl px-3 py-2 border text-xs font-medium flex-1 transition-all ${
                done    ? "bg-green-900/20 border-green-700/40 text-green-300"
                : active  ? "bg-cyan-900/20 border-cyan-700/40 text-cyan-300 animate-pulse"
                : failed  ? "bg-red-900/20 border-red-700/30 text-red-400"
                : "bg-white/5 border-white/10 text-gray-600"
              }`}>
                <span className={`w-4 h-4 rounded-full flex items-center justify-center shrink-0 text-[10px] font-bold ${
                  done ? "bg-green-500 text-black" : active ? "bg-cyan-500/30 border border-cyan-400" : "bg-white/10"
                }`}>
                  {done ? "✓" : i + 1}
                </span>
                {stage.label}
              </div>
              {i < STAGES.length - 1 && <div className={`w-6 h-px ${done ? "bg-green-700" : "bg-white/10"}`} />}
            </div>
          );
        })}
      </div>

      {/* Live stats */}
      <div className="flex gap-3 mb-4 w-full max-w-3xl">
        {[
          { label: "Nodes", count: nodeCount, color: "text-cyan-400 border-cyan-800 bg-cyan-900/10" },
          { label: "Edges", count: edgeCount, color: "text-purple-400 border-purple-800 bg-purple-900/10" },
          { label: "Personas", count: personaCount, color: "text-pink-400 border-pink-800 bg-pink-900/10" },
        ].map(({ label, count, color }) => (
          <div key={label} className={`flex-1 rounded-xl border px-4 py-3 text-center ${color}`}>
            <div className="text-2xl font-bold">{count}</div>
            <div className="text-xs opacity-70">{label}</div>
          </div>
        ))}
      </div>

      {/* Live event log */}
      <div className="w-full max-w-3xl flex-1 min-h-0 bg-black/50 border border-white/10 rounded-2xl overflow-hidden flex flex-col">
        <div className="flex items-center justify-between px-4 py-2 border-b border-white/10">
          <span className="text-xs font-mono text-gray-500">live event stream</span>
          <span className="text-xs font-mono text-gray-600">{logs.length} events</span>
        </div>
        <div className="flex-1 overflow-y-auto p-3 space-y-0.5 font-mono text-xs">
          {logs.length === 0 && (
            <p className="text-gray-700 text-center mt-8">Waiting for events…</p>
          )}
          {logs.map((log) => (
            <div key={log.id} className={`flex gap-2 ${LOG_STYLES[log.type] ?? "text-gray-400"}`}>
              <span className="text-gray-700 shrink-0 select-none">
                {new Date(log.timestamp).toLocaleTimeString("en-US", { hour12: false, hour: "2-digit", minute: "2-digit", second: "2-digit" })}
              </span>
              <span className="break-all">{log.message}</span>
            </div>
          ))}
          <div ref={logEndRef} />
        </div>
      </div>

      {/* Error detail */}
      {isError && statusData?.error_message && (
        <div className="w-full max-w-3xl mt-3 bg-red-900/20 border border-red-700/30 rounded-xl p-3">
          <p className="text-xs text-red-300 font-mono break-words">{statusData.error_message}</p>
          <p className="text-xs text-red-500 mt-1">Redirecting to upload in 4 seconds…</p>
        </div>
      )}
    </div>
  );
}
