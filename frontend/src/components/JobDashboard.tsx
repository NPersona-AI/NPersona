"use client";

import { useState, useRef } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useSSE } from "@/hooks/useSSE";
import { generatePersonas } from "@/lib/api";
import BuildingView from "./BuildingView";
import GraphView from "./GraphView";
import PersonasView from "./PersonasView";

export type JobStatus =
  | "unknown"
  | "parsing"
  | "graph_building"
  | "graph_ready"
  | "persona_generating"
  | "done"
  | "error";

export interface LogEntry {
  id: string;
  msg: string;
  type: string;
}

interface Props {
  jobId: string;
}

export default function JobDashboard({ jobId }: Props) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [status, setStatus] = useState<JobStatus>("unknown");
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [graphData, setGraphData] = useState<{ nodes: unknown[]; edges: unknown[] } | null>(null);
  const [personas, setPersonas] = useState<unknown[]>([]);
  const [coverage, setCoverage] = useState<unknown>(null);
  const [errorMsg, setErrorMsg] = useState("");
  const [numUser, setNumUser] = useState(() => parseInt(searchParams.get("u") ?? "5", 10));
  const [numAdv, setNumAdv] = useState(() => parseInt(searchParams.get("a") ?? "5", 10));
  const [generating, setGenerating] = useState(false);

  // Stable ref for persona counts so generate callback doesn't need deps
  const personaCountRef = useRef({ numUser, numAdv });
  personaCountRef.current = { numUser, numAdv };

  // Persists across SSE reconnects — once graph data is loaded, don't fetch again
  const graphDataRef = useRef<{ nodes: unknown[]; edges: unknown[] } | null>(null);
  // In-flight guard to avoid parallel fetches
  const graphFetchingRef = useRef(false);

  const pushLog = (msg: string, type = "info") =>
    setLogs((prev) => [
      ...prev,
      { id: Math.random().toString(36).slice(2, 9), msg, type },
    ]);

  // ── SSE handler ───────────────────────────────────────────────────────────
  useSSE(jobId, (event, data) => {
    switch (event) {
      case "stage_changed": {
        const stage = data.stage as JobStatus;
        setStatus(stage);
        pushLog(`► ${data.message}`, "stage");

        // Fetch graph once — skip if already have data or a fetch is in-flight
        if ((stage === "graph_ready" || stage === "persona_generating" || stage === "done")
            && !graphDataRef.current && !graphFetchingRef.current) {
          graphFetchingRef.current = true;
          fetch(`http://localhost:8001/api/job/${jobId}/graph`)
            .then((r) => r.ok ? r.json() : Promise.reject("not-ok"))
            .then((d) => {
              graphDataRef.current = d;
              setGraphData(d);
            })
            .catch(() => {
              graphFetchingRef.current = false; // allow retry on next event
            });
        }

        // Fetch personas + coverage when done (DB is committed before done fires)
        if (stage === "done") {
          fetch(`http://localhost:8001/api/job/${jobId}/personas`)
            .then((r) => r.json())
            .then((d) => {
              const all = [...(d.user_centric ?? []), ...(d.adversarial ?? [])];
              setPersonas(all);
            })
            .catch(() => {});

          fetch(`http://localhost:8001/api/job/${jobId}/coverage`)
            .then((r) => r.json())
            .then(setCoverage)
            .catch(() => {});
        }

        if (stage === "error") setErrorMsg(String(data.message ?? "Pipeline error"));
        break;
      }

      case "log_message":
        pushLog(String(data.message), "info");
        break;

      case "node_created":
        pushLog(
          `  node [${data.type}] ${data.label}  (${Number(data.index) + 1}/${data.total})`,
          "node"
        );
        break;

      case "edge_created":
        pushLog(
          `  edge  ${data.source} —[${data.type}]→ ${data.target}  (${Number(data.index) + 1}/${data.total})`,
          "edge"
        );
        break;

      case "persona_born":
        pushLog(
          `  persona  ${data.team === "adversarial" ? `attacker: ${data.alias ?? data.name}` : `user: ${data.name}`}`,
          "persona"
        );
        break;

      case "error":
        pushLog(`✕ ${data.message}`, "error");
        break;
    }
  });

  // ── Generate personas ──────────────────────────────────────────────────────
  const handleGenerate = async () => {
    const { numUser: u, numAdv: a } = personaCountRef.current;
    setGenerating(true);
    setStatus("persona_generating");
    pushLog(`► Starting persona generation (${u} user, ${a} adversarial)…`, "stage");
    try {
      await generatePersonas(jobId, u, a);
    } catch {
      setStatus("error");
      setErrorMsg("Failed to start persona generation");
    } finally {
      setGenerating(false);
    }
  };

  // ── Derived booleans ───────────────────────────────────────────────────────
  const isBuilding =
    status === "unknown" || status === "parsing" || status === "graph_building";
  const isGraphReady = status === "graph_ready";
  const isGenerating = status === "persona_generating";
  const isDone = status === "done";
  const isError = status === "error";

  // ── Render ─────────────────────────────────────────────────────────────────
  return (
    <div className="min-h-screen bg-[#050508] flex flex-col">
      {/* Top nav */}
      <header className="h-14 border-b border-white/[0.06] flex items-center px-6 gap-4 shrink-0">
        <button
          onClick={() => router.push("/upload")}
          className="text-xs font-mono text-gray-500 hover:text-white transition-colors"
        >
          ← NPersona
        </button>
        <span className="text-gray-700">|</span>
        <span className="text-xs font-mono text-gray-500 truncate max-w-xs">{jobId}</span>

        <div className="ml-auto flex items-center gap-2">
          {isBuilding && (
            <span className="flex items-center gap-1.5 text-xs text-yellow-400">
              <span className="w-1.5 h-1.5 rounded-full bg-yellow-400 animate-pulse" />
              {status === "unknown" ? "Connecting…" : status === "parsing" ? "Parsing…" : "Building graph…"}
            </span>
          )}
          {isGraphReady && (
            <span className="flex items-center gap-1.5 text-xs text-cyan-400">
              <span className="w-1.5 h-1.5 rounded-full bg-cyan-400" />
              Graph ready
            </span>
          )}
          {isGenerating && (
            <span className="flex items-center gap-1.5 text-xs text-pink-400">
              <span className="w-1.5 h-1.5 rounded-full bg-pink-400 animate-pulse" />
              Generating personas…
            </span>
          )}
          {isDone && (
            <span className="flex items-center gap-1.5 text-xs text-green-400">
              <span className="w-1.5 h-1.5 rounded-full bg-green-400" />
              Done
            </span>
          )}
          {isError && (
            <span className="flex items-center gap-1.5 text-xs text-red-400">
              <span className="w-1.5 h-1.5 rounded-full bg-red-400" />
              Error
            </span>
          )}
        </div>
      </header>

      {/* Main */}
      <main className="flex-1 overflow-hidden">
        {(isBuilding || isGenerating) && (
          <BuildingView status={status} logs={logs} />
        )}

        {isGraphReady && (
          <GraphView
            graphData={graphData}
            logs={logs}
            numUser={numUser}
            numAdv={numAdv}
            onNumUserChange={setNumUser}
            onNumAdvChange={setNumAdv}
            onGenerate={handleGenerate}
            generating={generating}
          />
        )}

        {isDone && (
          <PersonasView
            personas={personas as Record<string, unknown>[]}
            coverage={coverage}
            graphData={graphData}
            onReset={() => router.push("/upload")}
          />
        )}

        {isError && (
          <div className="flex flex-col items-center justify-center h-full gap-6 px-4">
            <div className="w-16 h-16 rounded-full bg-red-500/10 border border-red-500/30 flex items-center justify-center">
              <span className="text-2xl">✕</span>
            </div>
            <div className="text-center">
              <p className="text-lg font-semibold text-red-400 mb-2">Pipeline Error</p>
              <p className="text-sm text-gray-400 max-w-sm">{errorMsg}</p>
            </div>
            <button
              onClick={() => router.push("/upload")}
              className="px-6 py-3 rounded-xl border border-white/10 text-sm hover:bg-white/5 transition-colors"
            >
              Start over
            </button>
          </div>
        )}
      </main>
    </div>
  );
}
