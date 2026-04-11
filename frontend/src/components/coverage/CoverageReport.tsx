"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useQueryClient } from "@tanstack/react-query";
import { useAppStore, useHasHydrated } from "@/stores/appStore";
import { useJobCoverage, useGenerateMissing, getExportUrl } from "@/hooks/useApi";
import {
  CheckCircle2, AlertCircle, MinusCircle, Zap,
  Download, RefreshCw, ArrowLeft, Shield, User, LogOut
} from "lucide-react";

// ─── Types ────────────────────────────────────────────────────────────────────

interface CoverageEntry {
  taxonomy_id: string;
  name: string;
  category: string;
  description: string;
  team: string;
  owasp_mapping?: string;
  status: "covered" | "partial" | "missing";
  covered_by: string[];
  coverage_count: number;
}

interface CoverageData {
  total: number;
  covered: number;
  partial: number;
  missing: number;
  coverage_percentage: number;
  entries: CoverageEntry[];
}

// ─── Donut chart component ────────────────────────────────────────────────────

function CoverageDonut({ pct, covered, partial, missing }: {
  pct: number; covered: number; partial: number; missing: number;
}) {
  const r = 54;
  const circ = 2 * Math.PI * r;
  const coveredDash = (covered / (covered + partial + missing)) * circ;
  const partialDash = (partial / (covered + partial + missing)) * circ;

  return (
    <div className="relative w-36 h-36">
      <svg className="w-36 h-36 -rotate-90" viewBox="0 0 120 120">
        {/* Background */}
        <circle cx="60" cy="60" r={r} fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="12" />
        {/* Covered */}
        <circle cx="60" cy="60" r={r} fill="none" stroke="#00FF88" strokeWidth="12"
          strokeDasharray={`${coveredDash} ${circ}`} strokeLinecap="round" />
        {/* Partial */}
        <circle cx="60" cy="60" r={r} fill="none" stroke="#FF8800" strokeWidth="12"
          strokeDasharray={`${partialDash} ${circ}`}
          strokeDashoffset={-coveredDash}
          strokeLinecap="round" />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-2xl font-bold text-white">{pct.toFixed(0)}%</span>
        <span className="text-[10px] text-gray-400 uppercase tracking-wider">covered</span>
      </div>
    </div>
  );
}

// ─── Entry card ───────────────────────────────────────────────────────────────

function EntryCard({
  entry,
  onGenerateMissing,
  isGenerating,
}: {
  entry: CoverageEntry;
  onGenerateMissing: (id: string) => void;
  isGenerating: boolean;
}) {
  const [showRipple, setShowRipple] = useState(false);

  const statusConfig = {
    covered: { icon: CheckCircle2, color: "#00FF88", bg: "bg-[#00FF88]/10", border: "border-[#00FF88]/30", label: "Covered" },
    partial:  { icon: MinusCircle,  color: "#FF8800", bg: "bg-[#FF8800]/10", border: "border-[#FF8800]/30", label: "Partial" },
    missing:  { icon: AlertCircle,  color: "#FF007F", bg: "bg-[#FF007F]/10", border: "border-[#FF007F]/30", label: "Missing" },
  };

  const cfg = statusConfig[entry.status];
  const Icon = cfg.icon;
  const isAdv = entry.team === "adversarial";

  const handleGenerate = () => {
    setShowRipple(true);
    setTimeout(() => setShowRipple(false), 800);
    onGenerateMissing(entry.taxonomy_id);
  };

  return (
    <div className={`relative glass rounded-xl p-4 border ${cfg.border} overflow-hidden transition-all duration-300 hover:scale-[1.01]`}>
      {/* Ripple effect */}
      {showRipple && (
        <div className="absolute inset-0 animate-ping rounded-xl border-2 border-[#FF007F]/50 pointer-events-none" />
      )}

      <div className="flex items-start gap-3">
        {/* Status icon */}
        <div className={`mt-0.5 p-1.5 rounded-lg ${cfg.bg} shrink-0`}>
          <Icon size={14} style={{ color: cfg.color }} />
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-[10px] font-mono text-gray-500">{entry.taxonomy_id}</span>
            <h3 className="text-sm font-semibold text-white truncate">{entry.name}</h3>
            {/* Team icon */}
            {isAdv
              ? <Shield size={10} className="text-[#FF007F] shrink-0" />
              : <User size={10} className="text-[#00F0FF] shrink-0" />}
            {entry.owasp_mapping && (
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-yellow-900/20 border border-yellow-700/30 text-yellow-300">
                {entry.owasp_mapping}
              </span>
            )}
          </div>

          <p className="text-[11px] text-gray-400 mt-1 leading-relaxed">{entry.description}</p>

          {/* Covered by */}
          {entry.covered_by.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-2">
              {entry.covered_by.map((name) => (
                <span key={name} className={`text-[10px] px-1.5 py-0.5 rounded-full ${cfg.bg} border ${cfg.border}`} style={{ color: cfg.color }}>
                  {name}
                </span>
              ))}
            </div>
          )}
        </div>

        {/* Generate missing button */}
        {entry.status === "missing" && (
          <button
            onClick={handleGenerate}
            disabled={isGenerating}
            className="shrink-0 flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[11px] font-semibold bg-[#FF007F]/20 border border-[#FF007F]/40 text-[#FF007F] hover:bg-[#FF007F]/30 disabled:opacity-50 transition-all"
          >
            {isGenerating ? <RefreshCw size={12} className="animate-spin" /> : <Zap size={12} />}
            Generate
          </button>
        )}
      </div>
    </div>
  );
}

// ─── Main component ───────────────────────────────────────────────────────────

export default function CoverageReport() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const hasHydrated = useHasHydrated();
  const { jobId, setStep, resetJob } = useAppStore();
  const { data, isLoading, refetch } = useJobCoverage(jobId);
  const generateMissing = useGenerateMissing();

  const handleNewSession = () => {
    resetJob();
    localStorage.removeItem("npersona-store");
    router.replace("/upload");
  };

  const [activeFilter, setActiveFilter] = useState<"all" | "covered" | "partial" | "missing">("all");
  const [showExport, setShowExport] = useState(false);
  const [generatingId, setGeneratingId] = useState<string | null>(null);

  useEffect(() => { setStep(5); }, [setStep]);
  useEffect(() => {
    if (!hasHydrated) return;
    if (!jobId) router.replace("/upload");
  }, [hasHydrated, jobId, router]);

  const coverage: CoverageData | undefined = data;

  const handleGenerateMissing = async (taxonomyId: string) => {
    if (!jobId) return;
    setGeneratingId(taxonomyId);
    try {
      await generateMissing.mutateAsync({ jobId, taxonomyId });
      // Invalidate and refetch both coverage and personas
      await queryClient.invalidateQueries({ queryKey: ["coverage", jobId] });
      await queryClient.invalidateQueries({ queryKey: ["personas", jobId] });
      refetch();
    } catch (err) {
      alert("Failed to generate persona for this type");
    } finally {
      setGeneratingId(null);
    }
  };

  const filteredEntries = coverage?.entries.filter((e) =>
    activeFilter === "all" ? true : e.status === activeFilter
  ) || [];

  return (
    <div className="max-w-5xl mx-auto px-4 py-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-8 flex-wrap gap-4">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <button
              onClick={() => router.push("/personas")}
              className="text-gray-500 hover:text-white transition-colors"
            >
              <ArrowLeft size={16} />
            </button>
            <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-[#00FF88] via-white to-[#FF8800]">
              Coverage Report
            </h1>
          </div>
          <p className="text-gray-400 text-sm">OWASP LLM Top 10 + MITRE ATLAS taxonomy coverage analysis</p>
        </div>

        <button
          onClick={() => setShowExport(true)}
          className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold glass border border-white/10 hover:border-white/30 text-white transition-all"
        >
          <Download size={15} /> Export
        </button>
      </div>

      {isLoading && (
        <div className="flex items-center justify-center py-24">
          <div className="w-12 h-12 rounded-full border-2 border-[#00FF88]/30 border-t-[#00FF88] animate-spin" />
        </div>
      )}

      {coverage && (
        <>
          {/* Stats row */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
            {[
              { label: "Total Types", value: coverage.total, color: "text-white" },
              { label: "Covered",  value: coverage.covered,  color: "text-[#00FF88]" },
              { label: "Partial",  value: coverage.partial,  color: "text-[#FF8800]" },
              { label: "Missing",  value: coverage.missing,  color: "text-[#FF007F]" },
            ].map((stat) => (
              <div key={stat.label} className="glass rounded-xl p-4 text-center">
                <div className={`text-3xl font-bold font-mono ${stat.color}`}>{stat.value}</div>
                <div className="text-xs text-gray-500 mt-1 uppercase tracking-wider">{stat.label}</div>
              </div>
            ))}
          </div>

          {/* Donut + category filter */}
          <div className="flex flex-col sm:flex-row items-center gap-8 mb-8 glass rounded-2xl p-6">
            <CoverageDonut
              pct={coverage.coverage_percentage}
              covered={coverage.covered}
              partial={coverage.partial}
              missing={coverage.missing}
            />
            <div className="flex-1">
              <h3 className="font-semibold mb-3 text-sm uppercase tracking-wider text-gray-400">Filter by Status</h3>
              <div className="flex flex-wrap gap-2">
                {(["all", "covered", "partial", "missing"] as const).map((f) => (
                  <button
                    key={f}
                    onClick={() => setActiveFilter(f)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-semibold capitalize transition-all border ${
                      activeFilter === f
                        ? f === "all"
                          ? "bg-white/10 border-white/30 text-white"
                          : f === "covered"
                          ? "bg-[#00FF88]/20 border-[#00FF88]/50 text-[#00FF88]"
                          : f === "partial"
                          ? "bg-[#FF8800]/20 border-[#FF8800]/50 text-[#FF8800]"
                          : "bg-[#FF007F]/20 border-[#FF007F]/50 text-[#FF007F]"
                        : "border-white/10 text-gray-400 hover:border-white/20"
                    }`}
                  >
                    {f === "all" ? `All (${coverage.total})` :
                     f === "covered" ? `Covered (${coverage.covered})` :
                     f === "partial" ? `Partial (${coverage.partial})` :
                     `Missing (${coverage.missing})`}
                  </button>
                ))}
              </div>

              <div className="mt-4 flex gap-4 text-xs text-gray-500">
                <span className="flex items-center gap-1.5">
                  <Shield size={11} className="text-[#FF007F]" /> Adversarial
                </span>
                <span className="flex items-center gap-1.5">
                  <User size={11} className="text-[#00F0FF]" /> User-Centric
                </span>
              </div>
            </div>
          </div>

          {/* Entries grid */}
          <div className="grid grid-cols-1 gap-3">
            {filteredEntries.map((entry) => (
              <EntryCard
                key={entry.taxonomy_id}
                entry={entry}
                onGenerateMissing={handleGenerateMissing}
                isGenerating={generatingId === entry.taxonomy_id}
              />
            ))}
          </div>
        </>
      )}

      {/* Quit banner */}
      {coverage && (
        <div className="mt-10 glass rounded-2xl p-6 border border-white/5 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div>
            <p className="text-sm font-semibold text-white">Done with this session?</p>
            <p className="text-xs text-gray-500 mt-0.5">Export your report above, then start fresh with a new document.</p>
          </div>
          <button
            onClick={handleNewSession}
            className="shrink-0 flex items-center gap-2 px-5 py-2.5 rounded-xl bg-[#FF007F]/10 border border-[#FF007F]/30 text-[#FF007F] hover:bg-[#FF007F]/20 hover:border-[#FF007F]/50 text-sm font-semibold transition-all"
          >
            <LogOut size={15} />
            Quit &amp; Start New Session
          </button>
        </div>
      )}

      {/* Export Modal */}
      {showExport && jobId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <div className="glass rounded-2xl p-8 max-w-sm w-full mx-4 space-y-6">
            <h2 className="text-xl font-bold">Export Personas</h2>

            <div className="space-y-3">
              {[
                { label: "All personas (JSON)", url: getExportUrl(jobId, "json") },
                { label: "All personas (CSV)", url: getExportUrl(jobId, "csv") },
                { label: "User-centric only (JSON)", url: getExportUrl(jobId, "json", "user_centric") },
                { label: "Adversarial only (JSON)", url: getExportUrl(jobId, "json", "adversarial") },
              ].map((opt) => (
                <a
                  key={opt.label}
                  href={opt.url}
                  download
                  className="flex items-center gap-3 w-full px-4 py-3 rounded-xl glass border border-white/10 hover:border-white/30 text-sm text-white transition-all"
                >
                  <Download size={15} className="text-gray-400" />
                  {opt.label}
                </a>
              ))}
            </div>

            <button
              onClick={() => setShowExport(false)}
              className="w-full py-2.5 rounded-xl border border-white/10 text-gray-400 hover:text-white hover:border-white/30 text-sm transition-all"
            >
              Close
            </button>

            <div className="border-t border-white/10 pt-4">
              <button
                onClick={handleNewSession}
                className="w-full flex items-center justify-center gap-2 py-2.5 rounded-xl bg-[#FF007F]/10 border border-[#FF007F]/30 text-[#FF007F] hover:bg-[#FF007F]/20 hover:border-[#FF007F]/50 text-sm font-semibold transition-all"
              >
                <LogOut size={14} />
                Quit &amp; Start New Session
              </button>
              <p className="text-center text-[10px] text-gray-600 mt-2">Clears all state and returns to upload</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
