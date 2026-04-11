"use client";

import { useAppStore } from "@/stores/appStore";
import { User, Shield } from "lucide-react";

export default function GraphControls({
  onGeneratePersonas,
  isGenerating,
}: {
  onGeneratePersonas: () => void;
  isGenerating: boolean;
}) {
  const { graphData, numUserPersonas, numAdversarialPersonas } = useAppStore();

  const nodeCount = graphData?.nodes?.length || 0;
  const edgeCount = graphData?.edges?.length || 0;
  const total = numUserPersonas + numAdversarialPersonas;

  return (
    <div className="absolute top-4 left-4 z-10 w-64 space-y-4">
      {/* Stats Card */}
      <div className="glass rounded-xl p-4">
        <h3 className="text-sm font-bold uppercase tracking-wider text-gray-400 mb-2">Graph Stats</h3>
        <div className="flex justify-between items-center text-sm">
          <span>Nodes</span>
          <span className="font-mono text-user">{nodeCount}</span>
        </div>
        <div className="flex justify-between items-center text-sm mt-1">
          <span>Relationships</span>
          <span className="font-mono text-adv">{edgeCount}</span>
        </div>
      </div>

      {/* Persona Config Card */}
      <div className="glass rounded-xl p-4 space-y-3">
        <h3 className="text-sm font-bold uppercase tracking-wider text-gray-400">Persona Plan</h3>
        <div className="flex items-center justify-between text-sm">
          <span className="flex items-center gap-1.5 text-[#00F0FF]">
            <User size={13} /> User-Centric
          </span>
          <span className="font-mono font-bold text-[#00F0FF]">{numUserPersonas}</span>
        </div>
        <div className="flex items-center justify-between text-sm">
          <span className="flex items-center gap-1.5 text-[#FF007F]">
            <Shield size={13} /> Adversarial
          </span>
          <span className="font-mono font-bold text-[#FF007F]">{numAdversarialPersonas}</span>
        </div>
        <div className="border-t border-white/10 pt-2 flex justify-between text-xs text-gray-400">
          <span>Total</span>
          <span className="font-bold text-white">{total}</span>
        </div>
        <button
          onClick={onGeneratePersonas}
          disabled={isGenerating || nodeCount === 0}
          className={`w-full py-2.5 rounded-lg font-bold text-sm transition-all shadow-lg ${
            isGenerating || nodeCount === 0
              ? "bg-gray-800 text-gray-500 cursor-not-allowed"
              : "bg-gradient-to-r from-user/80 to-adv/80 hover:from-user hover:to-adv text-white"
          }`}
        >
          {isGenerating
            ? "Generating…"
            : `Generate ${total} Personas`}
        </button>
      </div>

      {/* Legend */}
      <div className="glass rounded-xl p-4">
        <h3 className="text-sm font-bold uppercase tracking-wider text-gray-400 mb-2">Legend</h3>
        <ul className="space-y-2 text-xs">
          <LegendItem color="#00F0FF" label="User Role" />
          <LegendItem color="#ffffff" label="AI Agent" />
          <LegendItem color="#a78bfa" label="Capability" />
          <LegendItem color="#FF8800" label="Sensitive Data" />
          <LegendItem color="#00FF88" label="Guardrail" />
          <LegendItem color="#FF007F" label="Attack Surface" />
        </ul>
      </div>
    </div>
  );
}

function LegendItem({ color, label }: { color: string; label: string }) {
  return (
    <li className="flex items-center gap-2">
      <span className="w-3 h-3 rounded-full shadow-[0_0_8px_currentColor]" style={{ color, backgroundColor: color }} />
      <span>{label}</span>
    </li>
  );
}
