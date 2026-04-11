"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useQueryClient } from "@tanstack/react-query";
import { useAppStore, useHasHydrated } from "@/stores/appStore";
import { useJobPersonas, useJobStatus } from "@/hooks/useApi";
import {
  Shield, User, ChevronDown, ChevronRight,
  AlertTriangle, Zap, Brain, Target, ArrowRight, Download, RefreshCw
} from "lucide-react";

// ─── Types ───────────────────────────────────────────────────────────────────

interface UserPersona {
  id: string;
  name: string;
  role?: string;
  tech_literacy?: string;
  domain_expertise?: string;
  emotional_state?: string;
  edge_case_behavior?: string;
  edge_case_taxonomy_id?: string;
  frustration_level?: number;
  typical_tasks?: string[];
  multi_turn_scenario?: { turn: number; context: string; prompt: string }[];
  conversation_trajectory?: any[];
  example_prompts?: string[];
  composite_score?: number;
  novelty_score?: number;
}

interface AdvPersona {
  id: string;
  name: string;
  alias?: string;
  description?: string;
  skill_level?: string;
  attack_taxonomy_ids?: string[];
  owasp_mapping?: string[];
  mitre_atlas_id?: string;
  target_agent?: string;
  motivation?: string;
  risk_severity?: string;
  persistence_level?: number;
  evasion_techniques?: string[];
  conversation_trajectory?: { turn: number; intent: string; prompt: string }[];
  playbook?: { step: number; action: string; content: string }[];
  example_prompts?: string[];
  composite_score?: number;
  risk_score?: number;
}

// ─── Sub-components ───────────────────────────────────────────────────────────

function RiskBadge({ level }: { level?: string }) {
  const colors: Record<string, string> = {
    critical: "bg-red-900/60 text-red-300 border-red-700/50",
    high:     "bg-orange-900/60 text-orange-300 border-orange-700/50",
    medium:   "bg-yellow-900/60 text-yellow-300 border-yellow-700/50",
    low:      "bg-gray-800 text-gray-300 border-gray-700",
  };
  return (
    <span className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded border ${colors[level || "medium"] || colors.medium}`}>
      {level || "medium"}
    </span>
  );
}

function SkillBadge({ level }: { level?: string }) {
  const labels: Record<string, string> = {
    nation_state: "Nation-State",
    expert: "Expert",
    intermediate: "Intermediate",
    script_kiddie: "Script Kiddie",
  };
  return (
    <span className="text-[10px] px-2 py-0.5 rounded bg-purple-900/40 border border-purple-700/30 text-purple-300 font-mono">
      {labels[level || ""] || level}
    </span>
  );
}

function TaxBadge({ id }: { id: string }) {
  const isAdv = id.startsWith("A");
  return (
    <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded ${isAdv ? "bg-[#FF007F]/20 text-[#FF007F] border border-[#FF007F]/30" : "bg-[#00F0FF]/20 text-[#00F0FF] border border-[#00F0FF]/30"}`}>
      {id}
    </span>
  );
}

function UserCard({
  persona,
  index,
}: {
  persona: UserPersona;
  index: number;
}) {
  const [expanded, setExpanded] = useState(false);
  const scenario = persona.conversation_trajectory || persona.multi_turn_scenario || [];

  return (
    <div
      className="glass rounded-xl border border-[#00F0FF]/20 overflow-hidden animate-float-in"
      style={{ animationDelay: `${index * 80}ms` }}
    >
      {/* Header */}
      <div className="p-4 flex items-start gap-3">
        <div className="w-10 h-10 rounded-full bg-[#00F0FF]/10 border border-[#00F0FF]/30 flex items-center justify-center shrink-0">
          <User size={18} className="text-user" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <h3 className="font-bold text-white truncate">{persona.name}</h3>
            {persona.edge_case_taxonomy_id && <TaxBadge id={persona.edge_case_taxonomy_id} />}
          </div>
          <p className="text-xs text-gray-400 mt-0.5">{persona.role}</p>
          {persona.frustration_level && (
            <div className="flex items-center gap-1 mt-1">
              <span className="text-[10px] text-gray-500">Frustration</span>
              <div className="flex gap-0.5">
                {Array.from({ length: 10 }).map((_, i) => (
                  <div
                    key={i}
                    className={`w-1.5 h-1.5 rounded-full ${i < persona.frustration_level! ? "bg-[#FF007F]" : "bg-gray-700"}`}
                  />
                ))}
              </div>
              <span className="text-[10px] text-gray-400">{persona.frustration_level}/10</span>
            </div>
          )}
        </div>
        <div className="flex flex-col items-end gap-1">
          {persona.composite_score !== undefined && (
            <span className="text-[10px] font-mono text-gray-400">Score: {persona.composite_score?.toFixed(1)}</span>
          )}
        </div>
      </div>

      {/* Edge case behavior */}
      {persona.edge_case_behavior && (
        <div className="px-4 pb-3">
          <p className="text-xs text-gray-300 leading-relaxed">{persona.edge_case_behavior}</p>
        </div>
      )}

      {/* Tech literacy & mode tags */}
      <div className="px-4 pb-3 flex flex-wrap gap-1.5">
        {persona.tech_literacy && (
          <span className="text-[10px] px-2 py-0.5 rounded bg-[#00F0FF]/10 border border-[#00F0FF]/20 text-[#00F0FF] font-mono">
            tech:{persona.tech_literacy}
          </span>
        )}
        {persona.emotional_state && (
          <span className="text-[10px] px-2 py-0.5 rounded bg-white/5 border border-white/10 text-gray-300">
            {persona.emotional_state}
          </span>
        )}
        {persona.domain_expertise && (
          <span className="text-[10px] px-2 py-0.5 rounded bg-white/5 border border-white/10 text-gray-300">
            {persona.domain_expertise}
          </span>
        )}
      </div>

      {/* Expand toggle */}
      {(scenario.length > 0 || (persona.example_prompts || []).length > 0) && (
        <>
          <button
            onClick={() => setExpanded(!expanded)}
            className="w-full flex items-center justify-between px-4 py-2 text-xs text-gray-500 hover:text-gray-300 border-t border-white/5 transition-colors"
          >
            <span>Multi-turn scenario ({scenario.length} turns)</span>
            {expanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
          </button>

          {expanded && (
            <div className="px-4 pb-4 space-y-3">
              {scenario.map((turn: any, i: number) => (
                <div key={i} className="flex gap-2">
                  <div className="w-5 h-5 rounded-full bg-[#00F0FF]/20 text-[#00F0FF] flex items-center justify-center text-[10px] font-bold shrink-0 mt-0.5">
                    {turn.turn || i + 1}
                  </div>
                  <div>
                    {turn.context && <p className="text-[10px] text-gray-500 mb-0.5">{turn.context}</p>}
                    <p className="text-xs text-gray-200 font-mono bg-black/30 rounded p-2">"{turn.prompt}"</p>
                  </div>
                </div>
              ))}

              {(persona.example_prompts || []).length > 0 && (
                <div>
                  <p className="text-[10px] text-gray-500 mb-1 uppercase tracking-wider">Example Prompts</p>
                  {persona.example_prompts!.slice(0, 2).map((p, i) => (
                    <p key={i} className="text-xs text-gray-300 font-mono bg-black/20 rounded p-1.5 mb-1">"{p}"</p>
                  ))}
                </div>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
}

function AdvCard({
  persona,
  index,
}: {
  persona: AdvPersona;
  index: number;
}) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div
      className="glass rounded-xl border border-[#FF007F]/20 overflow-hidden animate-float-in"
      style={{ animationDelay: `${index * 80}ms` }}
    >
      {/* Header */}
      <div className="p-4 flex items-start gap-3">
        <div className="w-10 h-10 rounded-full bg-[#FF007F]/10 border border-[#FF007F]/30 flex items-center justify-center shrink-0">
          <Shield size={18} className="text-adv" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <h3 className="font-bold text-white truncate">{persona.name}</h3>
            {persona.alias && (
              <span className="text-[10px] font-mono text-gray-400">aka "{persona.alias}"</span>
            )}
          </div>
          <div className="flex items-center gap-1.5 mt-1 flex-wrap">
            <RiskBadge level={persona.risk_severity} />
            {persona.skill_level && <SkillBadge level={persona.skill_level} />}
          </div>
        </div>
        {persona.composite_score !== undefined && (
          <span className="text-[10px] font-mono text-gray-400">Score: {persona.composite_score?.toFixed(1)}</span>
        )}
      </div>

      {/* Description */}
      {persona.description && (
        <div className="px-4 pb-3">
          <p className="text-xs text-gray-300 leading-relaxed">{persona.description}</p>
        </div>
      )}

      {/* Taxonomy badges */}
      <div className="px-4 pb-3 flex flex-wrap gap-1.5">
        {(persona.attack_taxonomy_ids || []).map((id) => (
          <TaxBadge key={id} id={id} />
        ))}
        {(persona.owasp_mapping || []).map((id) => (
          <span key={id} className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-yellow-900/20 border border-yellow-700/30 text-yellow-300">
            OWASP {id}
          </span>
        ))}
      </div>

      {/* Expand toggle */}
      {((persona.conversation_trajectory || []).length > 0 || (persona.playbook || []).length > 0) && (
        <>
          <button
            onClick={() => setExpanded(!expanded)}
            className="w-full flex items-center justify-between px-4 py-2 text-xs text-gray-500 hover:text-gray-300 border-t border-white/5 transition-colors"
          >
            <span>Attack trajectory + playbook</span>
            {expanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
          </button>

          {expanded && (
            <div className="px-4 pb-4 space-y-4">
              {/* Conversation trajectory */}
              {(persona.conversation_trajectory || []).length > 0 && (
                <div className="space-y-2">
                  <p className="text-[10px] uppercase tracking-wider text-gray-500">Attack Trajectory</p>
                  {(persona.conversation_trajectory || []).map((turn: any, i: number) => (
                    <div key={i} className="flex gap-2">
                      <div className="w-5 h-5 rounded-full bg-[#FF007F]/20 text-[#FF007F] flex items-center justify-center text-[10px] font-bold shrink-0 mt-0.5">
                        {turn.turn || i + 1}
                      </div>
                      <div className="flex-1 min-w-0">
                        {turn.intent && (
                          <span className="text-[10px] text-gray-500 uppercase tracking-wide">{turn.intent} · </span>
                        )}
                        <p className="text-xs text-gray-200 font-mono bg-black/30 rounded p-2 mt-0.5">"{turn.prompt}"</p>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Playbook */}
              {(persona.playbook || []).length > 0 && (
                <div className="space-y-2">
                  <p className="text-[10px] uppercase tracking-wider text-gray-500">Playbook Steps</p>
                  {(persona.playbook || []).slice(0, 3).map((step: any, i: number) => (
                    <div key={i} className="text-xs bg-black/30 rounded p-2 border-l-2 border-[#FF007F]/50">
                      <p className="font-mono text-gray-200">"{step.content}"</p>
                      {step.failure_indicator && (
                        <p className="text-[10px] text-red-400 mt-1">⚠ {step.failure_indicator}</p>
                      )}
                    </div>
                  ))}
                </div>
              )}

              {/* Evasion techniques */}
              {(persona.evasion_techniques || []).length > 0 && (
                <div>
                  <p className="text-[10px] uppercase tracking-wider text-gray-500 mb-1">Evasion</p>
                  <div className="flex flex-wrap gap-1">
                    {persona.evasion_techniques!.map((t, i) => (
                      <span key={i} className="text-[10px] px-1.5 py-0.5 rounded bg-purple-900/30 border border-purple-700/30 text-purple-300">
                        {t}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
}

// ─── Main Component ────────────────────────────────────────────────────────────

export default function PersonaPanel() {
  const router = useRouter();
  const hasHydrated = useHasHydrated();
  const { jobId, setStep, jobStatus, setJobStatus, numUserPersonas, numAdversarialPersonas } = useAppStore();
  const { data, isLoading, refetch } = useJobPersonas(jobId);
  const { data: statusData } = useJobStatus(jobId);
  const [retrying, setRetrying] = useState(false);

  // Sync polled status
  useEffect(() => {
    if (statusData?.status && statusData.status !== jobStatus) {
      setJobStatus(statusData.status);
    }
  }, [statusData, jobStatus, setJobStatus]);

  useEffect(() => {
    setStep(4);
  }, [setStep]);

  useEffect(() => {
    if (!hasHydrated) return;
    if (!jobId) router.replace("/upload");
  }, [hasHydrated, jobId, router]);

  // Keep polling until done
  useEffect(() => {
    if (jobStatus === "done") {
      refetch();
    }
  }, [jobStatus, refetch]);

  const userPersonas: UserPersona[] = data?.user_centric || [];
  const advPersonas: AdvPersona[] = data?.adversarial || [];
  const total = userPersonas.length + advPersonas.length;
  const isError = statusData?.status === "error";
  const isGenerating = statusData?.status === "persona_generating";

  const handleRetry = async () => {
    if (!jobId) return;
    setRetrying(true);
    try {
      const apiBase = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001/api";
      await fetch(`${apiBase}/job/${jobId}/generate-personas`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ num_user_personas: numUserPersonas, num_adversarial_personas: numAdversarialPersonas }),
      });
      setJobStatus("persona_generating");
    } finally {
      setRetrying(false);
    }
  };

  const goToCoverage = () => router.push("/coverage");

  return (
    <div className="max-w-[1400px] mx-auto px-4 py-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-8 flex-wrap gap-4">
        <div>
          <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-[#00F0FF] via-white to-[#FF007F]">
            Persona Arsenal
          </h1>
          <p className="text-gray-400 text-sm mt-1">
            {isLoading ? "Generating…" : `${userPersonas.length} user-centric · ${advPersonas.length} adversarial · ${total} total`}
          </p>
        </div>

        <div className="flex gap-3">
          {total > 0 && (
            <button
              onClick={goToCoverage}
              className="flex items-center gap-2 px-5 py-2.5 rounded-xl font-semibold text-sm bg-gradient-to-r from-[#00F0FF]/20 to-[#FF007F]/20 border border-white/10 text-white hover:border-white/30 transition-all"
            >
              Coverage Report <ArrowRight size={16} />
            </button>
          )}
        </div>
      </div>

      {/* Error state */}
      {isError && total === 0 && (
        <div className="flex flex-col items-center justify-center py-24 gap-4">
          <div className="w-16 h-16 rounded-full bg-red-900/20 border border-red-700/40 flex items-center justify-center">
            <AlertTriangle size={28} className="text-red-400" />
          </div>
          <p className="text-red-300 font-semibold">Persona generation failed</p>
          <p className="text-gray-500 text-xs max-w-md text-center">
            {statusData?.error_message?.includes("429")
              ? "API rate limit reached. Wait a few minutes then retry, or switch to a different API key."
              : statusData?.error_message || "An unexpected error occurred."}
          </p>
          <button
            onClick={handleRetry}
            disabled={retrying}
            className="flex items-center gap-2 px-5 py-2.5 rounded-xl font-semibold text-sm bg-gradient-to-r from-[#00F0FF]/80 to-[#FF007F]/80 hover:from-[#00F0FF] hover:to-[#FF007F] text-white transition-all disabled:opacity-50"
          >
            <RefreshCw size={16} className={retrying ? "animate-spin" : ""} />
            {retrying ? "Retrying…" : "Retry Generation"}
          </button>
        </div>
      )}

      {/* Generating spinner */}
      {(isLoading || isGenerating) && total === 0 && !isError && (
        <div className="flex flex-col items-center justify-center py-24 gap-4">
          <div className="relative">
            <div className="w-16 h-16 rounded-full border-2 border-[#00F0FF]/30 border-t-[#00F0FF] animate-spin" />
            <div className="absolute inset-0 w-16 h-16 rounded-full border-2 border-[#FF007F]/30 border-b-[#FF007F] animate-spin" style={{ animationDirection: "reverse", animationDuration: "1.2s" }} />
          </div>
          <p className="text-gray-400 text-sm">Generating personas…</p>
          <p className="text-gray-600 text-xs">This may take 30–60 seconds</p>
        </div>
      )}

      {/* Split view */}
      {(userPersonas.length > 0 || advPersonas.length > 0) && (
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
          {/* User-centric column */}
          <div>
            <div className="flex items-center gap-2 mb-4">
              <div className="w-3 h-3 rounded-full bg-[#00F0FF] shadow-[0_0_8px_#00F0FF]" />
              <h2 className="font-bold text-[#00F0FF] text-sm uppercase tracking-wider">
                User-Centric · {userPersonas.length} personas
              </h2>
            </div>
            <div className="space-y-4">
              {userPersonas.map((p, i) => (
                <UserCard key={p.id} persona={p} index={i} />
              ))}
            </div>
          </div>

          {/* Adversarial column */}
          <div>
            <div className="flex items-center gap-2 mb-4">
              <div className="w-3 h-3 rounded-full bg-[#FF007F] shadow-[0_0_8px_#FF007F]" />
              <h2 className="font-bold text-[#FF007F] text-sm uppercase tracking-wider">
                Adversarial · {advPersonas.length} personas
              </h2>
            </div>
            <div className="space-y-4">
              {advPersonas.map((p, i) => (
                <AdvCard key={p.id} persona={p} index={i} />
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
