"use client";

import { useState } from "react";
import {
  User, Shield, ChevronDown, ChevronRight, Download, RotateCcw,
  MessageSquare, Swords, Target, Copy, Check,
} from "lucide-react";
import dynamic from "next/dynamic";

const GraphCanvas = dynamic(() => import("./GraphCanvas"), { ssr: false });

type Persona = Record<string, unknown>;
type Coverage = Record<string, unknown>;

interface Props {
  personas: Persona[];
  coverage: Coverage | null;
  graphData: { nodes: unknown[]; edges: unknown[] } | null;
  onReset: () => void;
}

type Tab = "personas" | "coverage" | "graph";

// ── Copy button ────────────────────────────────────────────────────────────────
function CopyBtn({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  const copy = () => {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    });
  };
  return (
    <button
      onClick={copy}
      className="shrink-0 p-1 rounded hover:bg-white/10 text-gray-600 hover:text-gray-300 transition-colors"
      title="Copy prompt"
    >
      {copied ? <Check size={11} className="text-green-400" /> : <Copy size={11} />}
    </button>
  );
}

// ── Prompt block ───────────────────────────────────────────────────────────────
function PromptBlock({ label, text, accent }: { label?: string; text: string; accent: string }) {
  return (
    <div className="group relative rounded-lg border bg-black/40 p-3" style={{ borderColor: `${accent}25` }}>
      {label && (
        <p className="text-[9px] font-semibold uppercase tracking-widest mb-1.5" style={{ color: `${accent}90` }}>
          {label}
        </p>
      )}
      <p className="text-xs text-gray-200 font-mono leading-relaxed whitespace-pre-wrap break-words pr-6">{text}</p>
      <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity">
        <CopyBtn text={text} />
      </div>
    </div>
  );
}

// ── Persona Card ───────────────────────────────────────────────────────────────
function PersonaCard({ p, index }: { p: Persona; index: number }) {
  const [open, setOpen] = useState(false);
  const isAdv = p.team === "adversarial";
  const accent = isAdv ? "#FF007F" : "#00F0FF";
  const borderClass = isAdv ? "border-pink-500/20" : "border-cyan-500/20";
  const bgClass = isAdv ? "bg-pink-500/[0.03]" : "bg-cyan-500/[0.03]";

  const trajectory = Array.isArray(p.conversation_trajectory)
    ? (p.conversation_trajectory as Record<string, unknown>[])
    : [];

  const playbook = Array.isArray(p.playbook)
    ? (p.playbook as Record<string, unknown>[])
    : [];

  const examplePrompts = Array.isArray(p.example_prompts)
    ? (p.example_prompts as string[])
    : [];

  const taxonomyIds = isAdv
    ? (Array.isArray(p.attack_taxonomy_ids) ? (p.attack_taxonomy_ids as string[]) : [])
    : (p.edge_case_taxonomy_id ? [String(p.edge_case_taxonomy_id)] : []);

  return (
    <div
      className={`rounded-2xl border ${borderClass} ${bgClass} transition-all`}
      style={{ animationDelay: `${index * 30}ms` }}
    >
      {/* Header */}
      <button onClick={() => setOpen(!open)} className="w-full flex items-start gap-3 p-4 text-left">
        <div
          className="w-9 h-9 rounded-full flex items-center justify-center shrink-0 mt-0.5"
          style={{ background: `${accent}15`, border: `1px solid ${accent}30` }}
        >
          {isAdv ? <Shield size={15} style={{ color: accent }} /> : <User size={15} style={{ color: accent }} />}
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <p className="font-semibold text-sm text-white">{String(p.name ?? "Unnamed")}</p>
            {p.alias && (
              <span className="text-[10px] px-2 py-0.5 rounded-full font-mono"
                style={{ background: `${accent}15`, color: accent }}>
                {String(p.alias)}
              </span>
            )}
            {taxonomyIds.map((id) => (
              <span key={id} className="text-[9px] px-1.5 py-0.5 rounded font-mono bg-white/5 text-gray-500">
                {id}
              </span>
            ))}
          </div>
          <p className="text-xs text-gray-500 mt-0.5">{String(p.role ?? p.description ?? p.team)}</p>
          {isAdv && p.risk_severity && (
            <span className={`mt-1.5 inline-block text-[10px] px-2 py-0.5 rounded-full font-medium ${
              p.risk_severity === "critical" ? "bg-red-500/20 text-red-400" :
              p.risk_severity === "high"     ? "bg-orange-500/20 text-orange-400" :
              p.risk_severity === "medium"   ? "bg-yellow-500/20 text-yellow-400" :
                                               "bg-gray-500/20 text-gray-400"
            }`}>
              {String(p.risk_severity)} risk
            </span>
          )}
          {!isAdv && p.frustration_level && (
            <span className="mt-1.5 inline-block text-[10px] px-2 py-0.5 rounded-full bg-orange-500/10 text-orange-400">
              frustration {String(p.frustration_level)}/10
            </span>
          )}
        </div>

        <div className="shrink-0 text-gray-600 mt-1">
          {open ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
        </div>
      </button>

      {/* Expanded body */}
      {open && (
        <div className="px-4 pb-5 space-y-4 border-t border-white/[0.05] pt-4">

          {/* Description / edge case */}
          {(p.description || p.edge_case_behavior) && (
            <div>
              <p className="text-[10px] text-gray-500 uppercase tracking-widest mb-1.5">
                {isAdv ? "Description" : "Edge-Case Behavior"}
              </p>
              <p className="text-xs text-gray-400 leading-relaxed">
                {String(p.description ?? p.edge_case_behavior)}
              </p>
            </div>
          )}

          {/* ── EXAMPLE PROMPTS (most important) ── */}
          {examplePrompts.length > 0 && (
            <div>
              <p className="text-[10px] uppercase tracking-widest mb-2 flex items-center gap-1.5"
                style={{ color: accent }}>
                <MessageSquare size={10} />
                Example Prompts
              </p>
              <div className="space-y-2">
                {examplePrompts.map((prompt, i) => (
                  <PromptBlock key={i} label={`Prompt ${i + 1}`} text={prompt} accent={accent} />
                ))}
              </div>
            </div>
          )}

          {/* ── CONVERSATION TRAJECTORY / MULTI-TURN ── */}
          {trajectory.length > 0 && (
            <div>
              <p className="text-[10px] uppercase tracking-widest mb-2 flex items-center gap-1.5"
                style={{ color: accent }}>
                <Swords size={10} />
                {isAdv ? "Attack Conversation" : "Multi-Turn Scenario"}
              </p>
              <div className="space-y-2">
                {trajectory.map((turn, i) => {
                  const promptText = String(turn.prompt ?? turn.content ?? turn.message ?? "");
                  const label = isAdv
                    ? `Turn ${turn.turn ?? i + 1} · ${turn.intent ?? ""}`
                    : `Turn ${turn.turn ?? i + 1} · ${turn.context ?? ""}`;
                  return (
                    <PromptBlock key={i} label={label} text={promptText} accent={accent} />
                  );
                })}
              </div>
            </div>
          )}

          {/* ── PLAYBOOK (adversarial) ── */}
          {isAdv && playbook.length > 0 && (
            <div>
              <p className="text-[10px] uppercase tracking-widest mb-2 flex items-center gap-1.5"
                style={{ color: accent }}>
                <Target size={10} />
                Attack Playbook
              </p>
              <div className="space-y-2">
                {playbook.map((step, i) => {
                  const content = String(step.content ?? step.action ?? step.step ?? "");
                  const failureIndicator = step.failure_indicator ? String(step.failure_indicator) : null;
                  return (
                    <div key={i} className="rounded-lg border border-white/[0.06] bg-black/30 p-3 space-y-1.5">
                      <div className="flex items-start gap-2">
                        <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-white/5 text-gray-500 shrink-0 mt-0.5">
                          Step {step.step ?? i + 1}
                        </span>
                        <div className="flex-1 min-w-0 group relative">
                          <p className="text-xs font-mono text-gray-200 whitespace-pre-wrap break-words pr-6">{content}</p>
                          <div className="absolute top-0 right-0 opacity-0 group-hover:opacity-100 transition-opacity">
                            <CopyBtn text={content} />
                          </div>
                        </div>
                      </div>
                      {failureIndicator && (
                        <p className="text-[10px] text-red-400/70 pl-8">
                          ⚠ Fail: {failureIndicator}
                        </p>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Extra meta */}
          <div className="flex flex-wrap gap-x-6 gap-y-2 pt-1 border-t border-white/[0.05] text-[10px] text-gray-600">
            {p.skill_level && <span>Skill: <span className="text-gray-400">{String(p.skill_level)}</span></span>}
            {p.motivation && <span>Motivation: <span className="text-gray-400">{String(p.motivation)}</span></span>}
            {p.attack_strategy && <span>Strategy: <span className="text-gray-400">{String(p.attack_strategy)}</span></span>}
            {p.tech_literacy && <span>Tech literacy: <span className="text-gray-400">{String(p.tech_literacy)}</span></span>}
            {p.emotional_state && <span>State: <span className="text-gray-400">{String(p.emotional_state)}</span></span>}
            {p.source_node_id && <span>Node: <span className="text-gray-400 font-mono">{String(p.source_node_id)}</span></span>}
          </div>
        </div>
      )}
    </div>
  );
}

// ── Coverage table ─────────────────────────────────────────────────────────────
function CoverageTable({ coverage }: { coverage: Coverage }) {
  const entries = (coverage.entries ?? coverage.coverage ?? []) as Record<string, unknown>[];

  const statusIcon = (s: string) =>
    s === "covered" ? <span className="text-green-400 text-base">✓</span> :
    s === "partial"  ? <span className="text-yellow-400 text-base">◐</span> :
                       <span className="text-red-400 text-base">✗</span>;

  if (entries.length === 0) {
    return <p className="text-gray-500 text-sm text-center py-8">No coverage data available.</p>;
  }

  return (
    <div className="space-y-2">
      {entries.map((e, i) => (
        <div key={i} className="flex items-start gap-3 p-4 glass rounded-xl">
          <div className="shrink-0 mt-0.5">{statusIcon(String(e.status ?? "missing"))}</div>
          <div className="flex-1 min-w-0">
            <p className="font-medium text-sm text-white">{String(e.name ?? e.taxonomy_id ?? "Unknown")}</p>
            {e.category && <p className="text-xs text-gray-500">{String(e.category)}</p>}
            {e.description && <p className="text-xs text-gray-400 mt-1">{String(e.description)}</p>}
          </div>
          <span className={`text-xs px-2 py-0.5 rounded-full shrink-0 ${
            String(e.status) === "covered" ? "bg-green-500/10 text-green-400" :
            String(e.status) === "partial"  ? "bg-yellow-500/10 text-yellow-400" :
                                              "bg-red-500/10 text-red-400"
          }`}>
            {String(e.status ?? "missing")}
          </span>
        </div>
      ))}
    </div>
  );
}

// ── Main view ──────────────────────────────────────────────────────────────────
export default function PersonasView({ personas, coverage, graphData, onReset }: Props) {
  const [tab, setTab] = useState<Tab>("personas");
  const userPersonas = personas.filter((p) => p.team === "user_centric");
  const advPersonas  = personas.filter((p) => p.team === "adversarial");

  const handleExport = () => {
    const blob = new Blob([JSON.stringify(personas, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "personas.json";
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="flex flex-col" style={{ height: "calc(100vh - 3.5rem)" }}>
      {/* Toolbar */}
      <div className="flex items-center gap-2 px-6 py-3 border-b border-white/[0.06] shrink-0 flex-wrap">
        {(["personas", "coverage", "graph"] as Tab[]).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-1.5 rounded-xl text-sm capitalize transition-all ${
              tab === t ? "bg-white/10 text-white" : "text-gray-500 hover:text-gray-300"
            }`}
          >
            {t}
            {t === "personas" && personas.length > 0 && (
              <span className="ml-1.5 text-xs text-gray-500">({personas.length})</span>
            )}
          </button>
        ))}

        {/* Summary pills */}
        {personas.length > 0 && (
          <div className="flex items-center gap-2 ml-2">
            <span className="text-xs px-2 py-0.5 rounded-full bg-cyan-500/10 text-cyan-400">
              {userPersonas.length} user
            </span>
            <span className="text-xs px-2 py-0.5 rounded-full bg-pink-500/10 text-pink-400">
              {advPersonas.length} adversarial
            </span>
          </div>
        )}

        <div className="ml-auto flex items-center gap-2">
          <button
            onClick={handleExport}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl glass text-xs text-gray-400 hover:text-white transition-all"
          >
            <Download size={12} /> Export JSON
          </button>
          <button
            onClick={onReset}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl glass text-xs text-gray-400 hover:text-white transition-all"
          >
            <RotateCcw size={12} /> New session
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto">
        {tab === "personas" && (
          <div className="p-6">
            {personas.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-24 text-gray-600">
                <div className="w-12 h-12 border-2 border-white/10 border-t-white/30 rounded-full animate-spin mb-4" />
                <p>Loading personas…</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
                {/* User-centric column */}
                <div className="space-y-3">
                  <p className="text-xs text-cyan-400 uppercase tracking-widest mb-4 flex items-center gap-2">
                    <User size={12} /> User-Centric ({userPersonas.length})
                  </p>
                  {userPersonas.map((p, i) => (
                    <PersonaCard key={String(p.id ?? i)} p={p} index={i} />
                  ))}
                </div>

                {/* Adversarial column */}
                <div className="space-y-3">
                  <p className="text-xs text-pink-400 uppercase tracking-widest mb-4 flex items-center gap-2">
                    <Shield size={12} /> Adversarial ({advPersonas.length})
                  </p>
                  {advPersonas.map((p, i) => (
                    <PersonaCard key={String(p.id ?? i)} p={p} index={i} />
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {tab === "coverage" && (
          <div className="p-6 max-w-3xl mx-auto">
            {coverage ? (
              <CoverageTable coverage={coverage} />
            ) : (
              <p className="text-gray-500 text-sm text-center py-8">No coverage data.</p>
            )}
          </div>
        )}

        {tab === "graph" && (
          <div style={{ height: "calc(100vh - 7rem)" }}>
            {graphData ? (
              <GraphCanvas graphData={graphData} />
            ) : (
              <div className="flex items-center justify-center h-full text-gray-500 text-sm">
                Graph not available.
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
