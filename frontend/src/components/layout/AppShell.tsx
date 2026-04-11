"use client";

import StepProgress from "./StepProgress";
import LogPanel from "./LogPanel";

export default function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <>
      <StepProgress />
      <main className="flex-1 pt-24 min-h-screen relative">
        {children}
      </main>
      <LogPanel />
    </>
  );
}
