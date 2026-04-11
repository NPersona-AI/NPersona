"use client";

import { useAppStore } from "@/stores/appStore";
import { useEffect, useState } from "react";
import { ChevronUp, ChevronDown, Terminal } from "lucide-react";

export default function LogPanel() {
  const { logs, clearLogs } = useAppStore();
  const [isOpen, setIsOpen] = useState(false);

  // Auto-scroll to bottom
  useEffect(() => {
    if (isOpen) {
      const container = document.getElementById("log-container");
      if (container) container.scrollTop = container.scrollHeight;
    }
  }, [logs, isOpen]);

  if (logs.length === 0) return null;

  return (
    <div className="fixed bottom-0 right-0 left-0 sm:left-auto sm:right-6 sm:bottom-6 sm:w-[450px] z-50">
      <div className={`glass rounded-t-xl sm:rounded-xl overflow-hidden transition-all duration-300 ${isOpen ? "h-64" : "h-12"}`}>
        {/* Header */}
        <div 
          className="flex items-center justify-between p-3 cursor-pointer bg-black/40 hover:bg-black/60 transition-colors border-b border-white/5"
          onClick={() => setIsOpen(!isOpen)}
        >
          <div className="flex items-center gap-2 text-sm font-mono text-gray-300">
            <Terminal size={16} className="text-user" />
            <span>Terminal Logs ({logs.length})</span>
          </div>
          <div className="flex items-center gap-2">
            {isOpen && (
              <button 
                onClick={(e) => { e.stopPropagation(); clearLogs(); }}
                className="text-xs text-red-400 hover:text-red-300 px-2 py-1 rounded border border-red-500/30"
              >
                Clear
              </button>
            )}
            {isOpen ? <ChevronDown size={18} /> : <ChevronUp size={18} />}
          </div>
        </div>

        {/* Content */}
        {isOpen && (
          <div id="log-container" className="h-52 overflow-y-auto p-4 space-y-2 font-mono text-xs bg-black/80">
            {logs.map((log) => (
              <div key={log.id} className={`flex items-start gap-2 ${log.type === "error" ? "text-red-400" : log.type === "warning" ? "text-yellow-400" : "text-gray-300"}`}>
                <span className="text-gray-600 shrink-0">
                  [{log.timestamp.toLocaleTimeString()}]
                </span>
                <span className="break-words">{log.message}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
