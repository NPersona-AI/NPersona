"use client";

import { useState, useCallback, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useDropzone } from "react-dropzone";
import { UploadCloud, File as FileIcon, X, Sparkles, User, Shield, Minus, Plus } from "lucide-react";
import { useUploadDocument } from "@/hooks/useApi";
import { useAppStore } from "@/stores/appStore";
import { animations } from "@/lib/animations";

function CounterInput({
  value,
  onChange,
  min = 1,
  max = 30,
  color,
}: {
  value: number;
  onChange: (v: number) => void;
  min?: number;
  max?: number;
  color: "user" | "adv";
}) {
  const accent = color === "user" ? "#00F0FF" : "#FF007F";
  const clamp = (v: number) => Math.min(max, Math.max(min, v));

  return (
    <div className="flex items-center gap-3">
      <button
        onClick={() => onChange(clamp(value - 1))}
        disabled={value <= min}
        className="w-8 h-8 rounded-full flex items-center justify-center border border-white/10 hover:border-white/30 disabled:opacity-30 disabled:cursor-not-allowed transition-all"
        style={{ color: accent }}
      >
        <Minus size={14} />
      </button>

      <div className="relative w-16">
        <input
          type="number"
          min={min}
          max={max}
          value={value}
          onChange={(e) => onChange(clamp(parseInt(e.target.value) || min))}
          className="w-full text-center bg-black/40 border rounded-lg py-1.5 text-lg font-bold focus:outline-none transition-all"
          style={{ borderColor: `${accent}40`, color: accent }}
        />
      </div>

      <button
        onClick={() => onChange(clamp(value + 1))}
        disabled={value >= max}
        className="w-8 h-8 rounded-full flex items-center justify-center border border-white/10 hover:border-white/30 disabled:opacity-30 disabled:cursor-not-allowed transition-all"
        style={{ color: accent }}
      >
        <Plus size={14} />
      </button>
    </div>
  );
}

export default function UploadWizard() {
  const [file, setFile] = useState<File | null>(null);
  const [prompt, setPrompt] = useState("");
  const router = useRouter();

  const {
    setJobId, setStep, setJobStatus, resetJob,
    numUserPersonas, numAdversarialPersonas,
    setNumUserPersonas, setNumAdversarialPersonas,
  } = useAppStore();

  const uploadDoc = useUploadDocument();

  useEffect(() => {
    resetJob();
    animations.fadeIn(".upload-container", 0.2);
  }, [resetJob]);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) setFile(acceptedFiles[0]);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "application/pdf": [".pdf"],
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
      "text/markdown": [".md", ".markdown"],
      "text/plain": [".txt"],
    },
    maxFiles: 1,
  });

  const handleStart = async () => {
    if (!file) return;
    try {
      const res = await uploadDoc.mutateAsync({ file, prompt });
      setJobId(res.job_id);
      setJobStatus(null);
      router.push("/graph-builder");
    } catch (error) {
      console.error("Upload failed:", error);
      alert("Failed to upload document");
    }
  };

  const total = numUserPersonas + numAdversarialPersonas;

  return (
    <div className="upload-container max-w-2xl mx-auto mt-10 px-4 pb-16">
      <div className="text-center mb-10">
        <h1 className="text-4xl md:text-5xl font-bold mb-4 bg-clip-text text-transparent bg-gradient-to-r from-user via-white to-adv">
          Adversarial Persona Maker
        </h1>
        <p className="text-gray-400">
          Upload your AI system documentation to generate red-teaming and edge-case personas.
        </p>
      </div>

      <div className="glass rounded-2xl p-6 sm:p-8 space-y-8">

        {/* ── Step 1: Upload Zone ──────────────────────────────── */}
        <div>
          <h2 className="text-lg font-medium mb-3 flex items-center gap-2">
            <span className="w-6 h-6 rounded-full bg-white/10 text-xs flex items-center justify-center font-bold">1</span>
            Seed Document
          </h2>
          {!file ? (
            <div
              {...getRootProps()}
              className={`border-2 border-dashed rounded-xl p-10 flex flex-col items-center justify-center cursor-pointer transition-all duration-300 ${
                isDragActive ? "border-user bg-user/5" : "border-gray-600 hover:border-gray-400 hover:bg-white/5"
              }`}
            >
              <input {...getInputProps()} />
              <UploadCloud size={48} className="text-gray-400 mb-4" />
              <p className="font-medium text-lg mb-1">Drag & drop your file here</p>
              <p className="text-sm text-gray-400">Supports PDF, DOCX, MD, TXT</p>
            </div>
          ) : (
            <div className="glass rounded-xl p-4 flex items-center justify-between border border-user/30 bg-user/5">
              <div className="flex items-center gap-3">
                <FileIcon size={32} className="text-user" />
                <div>
                  <p className="font-medium">{file.name}</p>
                  <p className="text-xs text-gray-400">{(file.size / 1024).toFixed(1)} KB</p>
                </div>
              </div>
              <button
                onClick={() => setFile(null)}
                className="p-2 hover:bg-white/10 rounded-full transition-colors"
              >
                <X size={20} className="text-gray-400 hover:text-white" />
              </button>
            </div>
          )}
        </div>

        {/* ── Step 2: Persona Counts ───────────────────────────── */}
        <div>
          <h2 className="text-lg font-medium mb-4 flex items-center gap-2">
            <span className="w-6 h-6 rounded-full bg-white/10 text-xs flex items-center justify-center font-bold">2</span>
            Persona Configuration
          </h2>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">

            {/* User-Centric */}
            <div className="rounded-xl border border-[#00F0FF]/20 bg-[#00F0FF]/5 p-5 space-y-4">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-full bg-[#00F0FF]/10 border border-[#00F0FF]/30 flex items-center justify-center">
                  <User size={16} className="text-[#00F0FF]" />
                </div>
                <div>
                  <p className="font-semibold text-[#00F0FF] text-sm">User-Centric</p>
                  <p className="text-[10px] text-gray-500">Edge-case & usability</p>
                </div>
              </div>

              <CounterInput
                value={numUserPersonas}
                onChange={setNumUserPersonas}
                color="user"
              />

              <div className="space-y-1 text-[10px] text-gray-500">
                <p>• Ambiguous queries & typos</p>
                <p>• Accessibility edge cases</p>
                <p>• Multi-language & domain confusion</p>
                <p>• 3-turn frustration scenarios</p>
              </div>
            </div>

            {/* Adversarial */}
            <div className="rounded-xl border border-[#FF007F]/20 bg-[#FF007F]/5 p-5 space-y-4">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-full bg-[#FF007F]/10 border border-[#FF007F]/30 flex items-center justify-center">
                  <Shield size={16} className="text-[#FF007F]" />
                </div>
                <div>
                  <p className="font-semibold text-[#FF007F] text-sm">Adversarial</p>
                  <p className="text-[10px] text-gray-500">Red-team attack personas</p>
                </div>
              </div>

              <CounterInput
                value={numAdversarialPersonas}
                onChange={setNumAdversarialPersonas}
                color="adv"
              />

              <div className="space-y-1 text-[10px] text-gray-500">
                <p>• Prompt injection & jailbreaks</p>
                <p>• Data exfiltration attempts</p>
                <p>• Multi-turn attack trajectories</p>
                <p>• Concrete attack playbooks</p>
              </div>
            </div>
          </div>

          {/* Summary bar */}
          <div className="mt-4 rounded-xl bg-white/5 border border-white/10 px-4 py-3 flex items-center justify-between">
            <div className="flex items-center gap-4 text-sm">
              <span className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-[#00F0FF]" />
                <span className="text-gray-300">{numUserPersonas} user-centric</span>
              </span>
              <span className="text-gray-600">+</span>
              <span className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-[#FF007F]" />
                <span className="text-gray-300">{numAdversarialPersonas} adversarial</span>
              </span>
            </div>
            <span className="text-white font-bold text-sm">
              {total} total persona{total !== 1 ? "s" : ""}
            </span>
          </div>
        </div>

        {/* ── Step 3: Additional Context ───────────────────────── */}
        <div>
          <h2 className="text-lg font-medium mb-3 flex items-center gap-2">
            <span className="w-6 h-6 rounded-full bg-white/10 text-xs flex items-center justify-center font-bold">3</span>
            Additional Context
            <span className="text-xs text-gray-500 font-normal">(optional)</span>
          </h2>
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="E.g., Focus specifically on prompt injection vulnerabilities and non-technical HR users..."
            className="w-full bg-black/40 border border-white/10 rounded-xl p-4 text-sm focus:outline-none focus:border-user/50 focus:ring-1 focus:ring-user/50 transition-all resize-none h-28 text-gray-300 placeholder:text-gray-600"
          />
        </div>

        {/* ── Submit ────────────────────────────────────────────── */}
        <button
          onClick={handleStart}
          disabled={!file || uploadDoc.isPending}
          className={`w-full py-4 rounded-xl font-bold flex items-center justify-center gap-2 transition-all duration-300 ${
            !file
              ? "bg-gray-800 text-gray-500 cursor-not-allowed"
              : "bg-gradient-to-r from-user/80 to-adv/80 hover:from-user hover:to-adv text-white shadow-lg cursor-pointer"
          }`}
        >
          {uploadDoc.isPending ? (
            <span className="animate-pulse">Uploading & Processing…</span>
          ) : (
            <>
              <Sparkles size={20} />
              Generate {total} Persona{total !== 1 ? "s" : ""} from Knowledge Graph
            </>
          )}
        </button>

      </div>
    </div>
  );
}
