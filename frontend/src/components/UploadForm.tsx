"use client";

import { useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useDropzone } from "react-dropzone";
import { UploadCloud, FileText, X, Sparkles, User, Shield, Plus, Minus } from "lucide-react";
import { uploadDocument } from "@/lib/api";

function Counter({ value, onChange, min = 1, max = 30, color }: {
  value: number; onChange: (v: number) => void; min?: number; max?: number; color: "cyan" | "pink";
}) {
  const accent = color === "cyan" ? "#00F0FF" : "#FF007F";
  const clamp = (v: number) => Math.min(max, Math.max(min, v));
  return (
    <div className="flex items-center gap-3">
      <button
        onClick={() => onChange(clamp(value - 1))}
        disabled={value <= min}
        className="w-8 h-8 rounded-full border border-white/10 flex items-center justify-center hover:border-white/30 disabled:opacity-30 transition-all"
        style={{ color: accent }}
      >
        <Minus size={13} />
      </button>
      <input
        type="number" min={min} max={max} value={value}
        onChange={(e) => onChange(clamp(parseInt(e.target.value) || min))}
        className="w-14 text-center bg-black/40 border rounded-lg py-1.5 text-lg font-bold focus:outline-none transition-all"
        style={{ borderColor: `${accent}40`, color: accent }}
      />
      <button
        onClick={() => onChange(clamp(value + 1))}
        disabled={value >= max}
        className="w-8 h-8 rounded-full border border-white/10 flex items-center justify-center hover:border-white/30 disabled:opacity-30 transition-all"
        style={{ color: accent }}
      >
        <Plus size={13} />
      </button>
    </div>
  );
}

export default function UploadForm() {
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [prompt, setPrompt] = useState("");
  const [numUser, setNumUser] = useState(5);
  const [numAdv, setNumAdv] = useState(5);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const onDrop = useCallback((files: File[]) => {
    if (files[0]) setFile(files[0]);
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

  const handleSubmit = async () => {
    if (!file) return;
    setLoading(true);
    setError("");
    try {
      const { job_id } = await uploadDocument(file, prompt);
      router.push(`/job/${job_id}?u=${numUser}&a=${numAdv}`);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Upload failed");
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-4 py-16">
      {/* Header */}
      <div className="text-center mb-10 fade-up">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full glass text-xs text-cyan-400 mb-6 border border-cyan-500/20">
          <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse" />
          AI Red-Teaming Platform
        </div>
        <h1 className="text-5xl md:text-6xl font-bold mb-4 bg-gradient-to-r from-cyan-400 via-white to-pink-500 bg-clip-text text-transparent">
          NPersona
        </h1>
        <p className="text-gray-400 text-lg max-w-md mx-auto">
          Upload your AI system documentation to generate adversarial red-teaming personas.
        </p>
      </div>

      <div className="w-full max-w-xl glass rounded-3xl p-8 fade-up space-y-7">
        {/* Drop zone */}
        <div>
          <p className="text-sm font-medium text-gray-400 mb-3 uppercase tracking-widest">1 · Seed Document</p>
          {!file ? (
            <div
              {...getRootProps()}
              className={`border-2 border-dashed rounded-2xl p-10 flex flex-col items-center justify-center cursor-pointer transition-all duration-300 ${
                isDragActive
                  ? "border-cyan-400 bg-cyan-500/5"
                  : "border-white/10 hover:border-white/25 hover:bg-white/[0.02]"
              }`}
            >
              <input {...getInputProps()} />
              <UploadCloud size={40} className="text-gray-500 mb-3" />
              <p className="text-white font-medium mb-1">Drop your file here</p>
              <p className="text-xs text-gray-500">PDF · DOCX · MD · TXT</p>
            </div>
          ) : (
            <div className="flex items-center justify-between p-4 rounded-2xl border border-cyan-500/30 bg-cyan-500/5">
              <div className="flex items-center gap-3">
                <FileText size={28} className="text-cyan-400 shrink-0" />
                <div>
                  <p className="font-medium text-sm">{file.name}</p>
                  <p className="text-xs text-gray-500">{(file.size / 1024).toFixed(1)} KB</p>
                </div>
              </div>
              <button
                onClick={() => setFile(null)}
                className="p-2 rounded-full hover:bg-white/10 transition-colors text-gray-400 hover:text-white"
              >
                <X size={16} />
              </button>
            </div>
          )}
        </div>

        {/* Persona counts */}
        <div>
          <p className="text-sm font-medium text-gray-400 mb-4 uppercase tracking-widest">2 · Persona Configuration</p>
          <div className="grid grid-cols-2 gap-4">
            <div className="rounded-2xl p-5 border border-cyan-500/20 bg-cyan-500/5 space-y-3">
              <div className="flex items-center gap-2">
                <div className="w-7 h-7 rounded-full bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center">
                  <User size={14} className="text-cyan-400" />
                </div>
                <div>
                  <p className="text-xs font-semibold text-cyan-400">User-Centric</p>
                  <p className="text-[10px] text-gray-500">Edge-case & usability</p>
                </div>
              </div>
              <Counter value={numUser} onChange={setNumUser} color="cyan" />
            </div>

            <div className="rounded-2xl p-5 border border-pink-500/20 bg-pink-500/5 space-y-3">
              <div className="flex items-center gap-2">
                <div className="w-7 h-7 rounded-full bg-pink-500/10 border border-pink-500/30 flex items-center justify-center">
                  <Shield size={14} className="text-pink-400" />
                </div>
                <div>
                  <p className="text-xs font-semibold text-pink-400">Adversarial</p>
                  <p className="text-[10px] text-gray-500">Red-team attacks</p>
                </div>
              </div>
              <Counter value={numAdv} onChange={setNumAdv} color="pink" />
            </div>
          </div>

          <div className="mt-3 px-4 py-2.5 rounded-xl bg-white/5 border border-white/8 flex items-center justify-between text-sm">
            <div className="flex items-center gap-3 text-gray-400">
              <span className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-cyan-400" />
                {numUser} user
              </span>
              <span>+</span>
              <span className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-pink-500" />
                {numAdv} adversarial
              </span>
            </div>
            <span className="text-white font-semibold">{numUser + numAdv} total</span>
          </div>
        </div>

        {/* Optional prompt */}
        <div>
          <p className="text-sm font-medium text-gray-400 mb-3 uppercase tracking-widest">
            3 · Context <span className="normal-case text-gray-600">(optional)</span>
          </p>
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="E.g. Focus on prompt injection and non-technical HR users…"
            className="w-full bg-black/40 border border-white/10 rounded-xl p-4 text-sm text-gray-300 placeholder:text-gray-600 focus:outline-none focus:border-cyan-500/40 transition-all resize-none h-24"
          />
        </div>

        {error && (
          <p className="text-red-400 text-sm bg-red-500/10 border border-red-500/20 rounded-xl px-4 py-3">{error}</p>
        )}

        <button
          onClick={handleSubmit}
          disabled={!file || loading}
          className={`w-full py-4 rounded-2xl font-semibold text-base flex items-center justify-center gap-2 transition-all duration-300 ${
            !file
              ? "bg-white/5 text-gray-600 cursor-not-allowed"
              : "bg-gradient-to-r from-cyan-500/80 to-pink-500/80 hover:from-cyan-500 hover:to-pink-500 text-white shadow-lg hover:shadow-cyan-500/25"
          }`}
        >
          {loading ? (
            <span className="flex items-center gap-2">
              <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              Uploading…
            </span>
          ) : (
            <>
              <Sparkles size={18} />
              Generate {numUser + numAdv} Personas
            </>
          )}
        </button>
      </div>
    </div>
  );
}
