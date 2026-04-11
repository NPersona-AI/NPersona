"use client";

import { useEffect, useRef } from "react";
import type { LogEntry, JobStatus } from "./JobDashboard";

const STAGES: { key: JobStatus; label: string }[] = [
  { key: "parsing",        label: "Parse document" },
  { key: "graph_building", label: "Build knowledge graph" },
  { key: "graph_ready",    label: "Graph ready" },
  { key: "persona_generating", label: "Generate personas" },
  { key: "done",           label: "Complete" },
];

const ORDER: JobStatus[] = ["parsing", "graph_building", "graph_ready", "persona_generating", "done"];

const LOG_CLASS: Record<string, string> = {
  stage:   "log-stage",
  node:    "log-node",
  edge:    "log-edge",
  persona: "log-persona",
  success: "log-success",
  error:   "log-error",
  info:    "log-info",
};

interface Props {
  status: JobStatus;
  logs: LogEntry[];
}

export default function BuildingView({ status, logs }: Props) {
  const logRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (logRef.current) {
      logRef.current.scrollTop = logRef.current.scrollHeight;
    }
  }, [logs]);

  const currentIdx = ORDER.indexOf(status);

  return (
    <div className="flex h-full" style={{ height: "calc(100vh - 3.5rem)" }}>
      {/* Left panel — progress */}
      <div className="w-72 shrink-0 border-r border-white/[0.06] flex flex-col p-6 gap-8">
        {/* Animated orb */}
        <div className="flex items-center justify-center py-6">
          <div className="relative w-24 h-24">
            <div className="absolute inset-0 rounded-full border-2 border-cyan-500/20 spin-slow" />
            <div className="absolute inset-2 rounded-full border border-cyan-500/30" style={{ animationDelay: "0.5s" }} />
            <div className="absolute inset-0 rounded-full bg-cyan-500/5 flex items-center justify-center">
              <div className="w-3 h-3 rounded-full bg-cyan-400 animate-pulse" />
            </div>
          </div>
        </div>

        {/* Stage list */}
        <div className="space-y-4">
          {STAGES.map((s, i) => {
            const done = i < currentIdx;
            const active = i === currentIdx;
            return (
              <div key={s.key} className="flex items-center gap-3">
                <div className={`w-6 h-6 rounded-full border flex items-center justify-center shrink-0 transition-all ${
                  done   ? "bg-cyan-500 border-cyan-500" :
                  active ? "border-cyan-400 bg-cyan-500/10" :
                           "border-white/10 bg-transparent"
                }`}>
                  {done ? (
                    <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                    </svg>
                  ) : active ? (
                    <div className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
                  ) : (
                    <div className="w-2 h-2 rounded-full bg-white/10" />
                  )}
                </div>
                <span className={`text-sm transition-all ${
                  done   ? "text-gray-400 line-through" :
                  active ? "text-white font-medium" :
                           "text-gray-600"
                }`}>
                  {s.label}
                </span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Right panel — live logs */}
      <div className="flex-1 flex flex-col">
        <div className="px-6 py-4 border-b border-white/[0.06] flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
          <span className="text-xs font-mono text-gray-400 uppercase tracking-widest">Live output</span>
        </div>

        <div
          ref={logRef}
          className="flex-1 overflow-y-auto p-6 font-mono text-xs space-y-1"
          style={{ scrollBehavior: "smooth" }}
        >
          {logs.length === 0 ? (
            <p className="text-gray-600">Waiting for pipeline output…</p>
          ) : (
            logs.map((log) => (
              <p key={log.id} className={LOG_CLASS[log.type] ?? "log-info"}>
                {log.msg}
              </p>
            ))
          )}
          <div className="h-1" />
        </div>
      </div>
    </div>
  );
}
