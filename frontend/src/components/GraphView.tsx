"use client";

import dynamic from "next/dynamic";
import { User, Shield, Minus, Plus, Sparkles, ChevronRight } from "lucide-react";
import type { LogEntry } from "./JobDashboard";
import { useEffect, useRef, useState } from "react";

const GraphCanvas = dynamic(() => import("./GraphCanvas"), {
  ssr: false,
  loading: () => (
    <div className="flex items-center justify-center w-full h-full">
      <div className="w-10 h-10 border-2 border-cyan-500/30 border-t-cyan-400 rounded-full animate-spin" />
    </div>
  ),
});

const LOG_CLASS: Record<string, string> = {
  stage: "log-stage", node: "log-node", edge: "log-edge",
  persona: "log-persona", success: "log-success", error: "log-error", info: "log-info",
};

interface Props {
  graphData: { nodes: unknown[]; edges: unknown[] } | null;
  logs: LogEntry[];
  numUser: number;
  numAdv: number;
  onNumUserChange: (n: number) => void;
  onNumAdvChange: (n: number) => void;
  onGenerate: () => void;
  generating: boolean;
}

function Counter({ value, onChange, color }: { value: number; onChange: (v: number) => void; color: "cyan" | "pink" }) {
  const accent = color === "cyan" ? "#00F0FF" : "#FF007F";
  const clamp = (v: number) => Math.min(100, Math.max(1, v));
  return (
    <div className="flex items-center gap-2">
      <button
        onClick={() => onChange(clamp(value - 5))}
        disabled={value <= 1}
        className="w-8 h-8 rounded-full border border-white/10 flex items-center justify-center hover:border-white/25 disabled:opacity-30 transition-all text-xs"
        style={{ color: accent }}
      >
        -5
      </button>
      <button
        onClick={() => onChange(clamp(value - 1))}
        disabled={value <= 1}
        className="w-8 h-8 rounded-full border border-white/10 flex items-center justify-center hover:border-white/25 disabled:opacity-30 transition-all"
        style={{ color: accent }}
      >
        <Minus size={12} />
      </button>
      <span className="text-xl font-bold w-12 text-center" style={{ color: accent }}>{value}</span>
      <button
        onClick={() => onChange(clamp(value + 1))}
        disabled={value >= 100}
        className="w-8 h-8 rounded-full border border-white/10 flex items-center justify-center hover:border-white/25 disabled:opacity-30 transition-all"
        style={{ color: accent }}
      >
        <Plus size={12} />
      </button>
      <button
        onClick={() => onChange(clamp(value + 5))}
        disabled={value >= 100}
        className="w-8 h-8 rounded-full border border-white/10 flex items-center justify-center hover:border-white/25 disabled:opacity-30 transition-all text-xs"
        style={{ color: accent }}
      >
        +5
      </button>
    </div>
  );
}

export default function GraphView({ graphData, logs, numUser, numAdv, onNumUserChange, onNumAdvChange, onGenerate, generating }: Props) {
  const logRef = useRef<HTMLDivElement>(null);
  const [showLog, setShowLog] = useState(false);

  useEffect(() => {
    if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight;
  }, [logs]);

  return (
    <div className="flex flex-col" style={{ height: "calc(100vh - 3.5rem)" }}>
      {/* ── Generate Personas Banner ── */}
      <div className="shrink-0 border-b border-cyan-500/20 bg-gradient-to-r from-cyan-950/60 via-black/40 to-pink-950/60 px-6 py-4">
        <div className="max-w-5xl mx-auto flex items-center gap-6 flex-wrap">
          {/* Status pill */}
          <div className="flex items-center gap-2 text-sm text-cyan-400 font-medium">
            <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
            Graph ready — configure and generate personas
          </div>

          <div className="flex items-center gap-6 flex-1 flex-wrap">
            {/* User-centric counter */}
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-1.5 text-xs text-gray-400">
                <User size={12} className="text-cyan-400" />
                User-Centric
              </div>
              <Counter value={numUser} onChange={onNumUserChange} color="cyan" />
            </div>

            {/* Adversarial counter */}
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-1.5 text-xs text-gray-400">
                <Shield size={12} className="text-pink-400" />
                Adversarial
              </div>
              <Counter value={numAdv} onChange={onNumAdvChange} color="pink" />
            </div>

            {/* Total badge */}
            <div className="text-xs text-gray-500 px-3 py-1 rounded-full border border-white/10 bg-white/5">
              {numUser + numAdv} total
            </div>

            {/* Generate button */}
            <button
              onClick={onGenerate}
              disabled={generating}
              className="ml-auto flex items-center gap-2 px-6 py-2.5 rounded-xl font-semibold text-sm bg-gradient-to-r from-cyan-500 to-pink-500 hover:from-cyan-400 hover:to-pink-400 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg shadow-cyan-500/20 hover:shadow-cyan-500/30"
            >
              {generating ? (
                <>
                  <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Starting…
                </>
              ) : (
                <>
                  <Sparkles size={15} />
                  Generate {numUser + numAdv} Personas
                  <ChevronRight size={14} />
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* ── Graph + sidebar ── */}
      <div className="flex flex-1 overflow-hidden">
        {/* Graph canvas */}
        <div className="flex-1 relative">
          {graphData ? (
            <GraphCanvas graphData={graphData} />
          ) : (
            <div className="flex items-center justify-center w-full h-full">
              <div className="w-10 h-10 border-2 border-cyan-500/30 border-t-cyan-400 rounded-full animate-spin" />
            </div>
          )}

          {/* Legend overlay */}
          <div className="absolute top-4 left-4 glass rounded-xl p-3 space-y-1.5 text-xs">
            {[
              { label: "User Role",      color: "#00F0FF" },
              { label: "Agent",          color: "#a78bfa" },
              { label: "Capability",     color: "#4ade80" },
              { label: "Sensitive Data", color: "#fb923c" },
              { label: "Guardrail",      color: "#facc15" },
              { label: "Attack Surface", color: "#f87171" },
            ].map((n) => (
              <div key={n.label} className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full shrink-0" style={{ background: n.color }} />
                <span className="text-gray-400">{n.label}</span>
              </div>
            ))}
          </div>

          {/* Stats overlay */}
          {graphData && (
            <div className="absolute top-4 right-4 glass rounded-xl px-4 py-3 text-xs text-gray-400 space-y-1">
              <p><span className="text-white font-semibold">{(graphData.nodes as unknown[]).length}</span> nodes</p>
              <p><span className="text-white font-semibold">{(graphData.edges as unknown[]).length}</span> edges</p>
            </div>
          )}

          {/* Build log toggle */}
          <button
            onClick={() => setShowLog((v) => !v)}
            className="absolute bottom-4 right-4 glass rounded-xl px-3 py-2 text-xs text-gray-400 hover:text-white transition-colors border border-white/[0.06]"
          >
            {showLog ? "Hide log" : "Show build log"}
          </button>

          {/* Slide-in log panel */}
          {showLog && (
            <div className="absolute bottom-14 right-4 w-80 h-64 glass rounded-xl border border-white/[0.06] flex flex-col overflow-hidden">
              <p className="px-4 py-2 text-xs text-gray-500 uppercase tracking-widest border-b border-white/[0.06] shrink-0">Build log</p>
              <div ref={logRef} className="flex-1 overflow-y-auto px-4 py-2 font-mono text-[11px] space-y-0.5">
                {logs.map((log) => (
                  <p key={log.id} className={LOG_CLASS[log.type] ?? "log-info"}>{log.msg}</p>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
